import uuid
import time
import logging
from typing import Dict, List, Optional
from shared.models.game_models import (
    GameState, Player, Hero, Building, Unit, Enemy, Position, 
    HeroType, BuildingType, TileType, Resources, MovementTarget, TargetType
)
from shared.constants.game_constants import (
    MAP_WIDTH, MAP_HEIGHT, HERO_TYPES, BUILDING_TYPES, 
    RESOURCE_TICK_RATE, WAVE_SPAWN_INTERVAL, ENEMY_SPAWN_CORNERS
)
from server.services.map_generator import MapGenerator
from server.services.pathfinding import Pathfinder

logger = logging.getLogger(__name__)

class GameManager:
    def __init__(self, lobby_id: str, players: Dict[str, Player]):
        self.lobby_id = lobby_id
        self.game_state = GameState(
            lobby_id=lobby_id,
            players=players,
            heroes={},
            buildings={},
            units={},
            enemies={},
            map_data=[],
            fog_of_war=[],
            game_time=0.0,
            is_active=True
        )
        
        self.last_resource_tick = time.time()
        self.last_wave_spawn = time.time()
        self.wave_number = 0
        self.pathfinder = Pathfinder(MAP_WIDTH, MAP_HEIGHT)
        self.enemy_paths = {}
        
        # Movement and tick system  
        self.hero_targets: Dict[str, MovementTarget] = {}  # Store movement targets for heroes
        self.hero_paths: Dict[str, List[Position]] = {}   # Store current paths for heroes
        self.last_update = time.time()
        self.tick_rate = 60  # 60 FPS server tick rate
        self.network_update_rate = 20  # Send updates to clients 20 times per second
        self.last_network_update = time.time()
        self.state_changed = False
        
        self._initialize_game()
    
    def _initialize_game(self):
        # Use lobby_id hash as seed to ensure all players get the same map
        seed = hash(self.lobby_id) % (2**32)
        logger.info(f"Initializing game for lobby {self.lobby_id} with map seed: {seed}")
        
        map_generator = MapGenerator(seed=seed)
        self.game_state.map_data = map_generator.generate_map()
        
        spawn_area = map_generator.get_spawn_area()
        center_x = (spawn_area[0] + spawn_area[2]) // 2
        center_y = (spawn_area[1] + spawn_area[3]) // 2
        
        town_hall_id = str(uuid.uuid4())
        self.game_state.buildings[town_hall_id] = Building(
            id=town_hall_id,
            building_type=BuildingType.TOWN_HALL,
            position=Position(x=center_x, y=center_y),
            health=1000,
            max_health=1000,
            player_id="shared",
            size=(3, 3)
        )
        
        hero_positions = [
            (center_x - 2, center_y - 2),
            (center_x + 2, center_y - 2),
            (center_x - 2, center_y + 2),
            (center_x + 2, center_y + 2)
        ]
        
        for i, (player_id, player) in enumerate(self.game_state.players.items()):
            if i < len(hero_positions):
                hero_id = str(uuid.uuid4())
                pos_x, pos_y = hero_positions[i]
                hero_stats = HERO_TYPES[player.hero_type]
                
                self.game_state.heroes[hero_id] = Hero(
                    id=hero_id,
                    player_id=player_id,
                    hero_type=player.hero_type,
                    position=Position(x=pos_x, y=pos_y),
                    health=hero_stats["health"],
                    max_health=hero_stats["health"]
                )
        
        # Initialize shared fog of war for all players
        self.game_state.fog_of_war = [
            [False for _ in range(MAP_WIDTH)] for _ in range(MAP_HEIGHT)
        ]
        
        # Update vision for all players initially
        for player_id in self.game_state.players:
            self._update_vision(player_id)
    
    def update(self) -> Optional[GameState]:
        current_time = time.time()
        dt = current_time - self.last_update
        self.last_update = current_time
        
        # Update game logic at 60 FPS
        if dt >= 1.0 / self.tick_rate:
            self.game_state.game_time += dt
            
            # Update hero movements
            self._update_hero_movements(dt)
            
            # Resource updates every 2 seconds
            if current_time - self.last_resource_tick >= RESOURCE_TICK_RATE:
                self._update_resources()
                self.last_resource_tick = current_time
                self.state_changed = True
            
            # Wave spawning
            if current_time - self.last_wave_spawn >= WAVE_SPAWN_INTERVAL:
                self._spawn_enemy_wave()
                self.last_wave_spawn = current_time
                self.state_changed = True
            
            # Update enemies
            self._update_enemies()
            
            # Clean up expired pings
            self._cleanup_expired_pings(current_time)
            
            self._check_game_over()
        
        # Return state only if something changed and enough time passed for network update
        if self.state_changed and (current_time - self.last_network_update >= 1.0 / self.network_update_rate):
            self.last_network_update = current_time
            self.state_changed = False
            return self.game_state
        
        return None
    
    def _update_hero_movements(self, dt: float):
        """Update hero positions using pathfinding"""
        for hero_id, hero in self.game_state.heroes.items():
            if hero_id not in self.hero_targets:
                continue
                
            target = self.hero_targets[hero_id]
            
            # Update target position if following a dynamic entity
            if target.target_type != TargetType.POSITION and target.target_id:
                new_target_pos = self._get_target_position(target)
                if new_target_pos:
                    # Check if target moved significantly
                    if (abs(new_target_pos.x - target.position.x) > 0.5 or 
                        abs(new_target_pos.y - target.position.y) > 0.5):
                        target.position = new_target_pos
                        # Recalculate path if target moved
                        self._calculate_path_to_target(hero_id, hero, target)
                else:
                    # Target no longer exists, stop movement
                    del self.hero_targets[hero_id]
                    if hero_id in self.hero_paths:
                        del self.hero_paths[hero_id]
                    continue
            
            # Get or calculate path
            if hero_id not in self.hero_paths:
                self._calculate_path_to_target(hero_id, hero, target)
            
            path = self.hero_paths.get(hero_id, [])
            if not path:
                # No valid path, remove target
                del self.hero_targets[hero_id]
                continue
            
            # Move along path
            hero_stats = HERO_TYPES[hero.hero_type.value]
            speed = hero_stats["speed"]  # tiles per second
            
            while path and len(path) > 0:
                next_pos = path[0]
                
                # Calculate direction and distance to next waypoint
                dx = next_pos.x - hero.position.x
                dy = next_pos.y - hero.position.y
                distance = (dx * dx + dy * dy) ** 0.5
                
                if distance <= 0.1:  # Reached waypoint
                    path.pop(0)  # Remove reached waypoint
                    continue
                
                # Move towards waypoint
                move_distance = speed * dt
                if move_distance >= distance:
                    # Reached this waypoint
                    hero.position.x = next_pos.x
                    hero.position.y = next_pos.y
                    path.pop(0)
                else:
                    # Move towards waypoint
                    move_x = (dx / distance) * move_distance
                    move_y = (dy / distance) * move_distance
                    
                    # Check for dynamic obstacles (other heroes, enemies)
                    new_x = hero.position.x + move_x
                    new_y = hero.position.y + move_y
                    
                    if self._is_dynamic_obstacle_at(new_x, new_y, hero_id):
                        # Recalculate path to avoid dynamic obstacle
                        self._calculate_path_to_target(hero_id, hero, target)
                        break
                    
                    hero.position.x = new_x
                    hero.position.y = new_y
                    
                    # Ensure hero stays within map bounds
                    hero.position.x = max(0.5, min(MAP_WIDTH - 0.5, hero.position.x))
                    hero.position.y = max(0.5, min(MAP_HEIGHT - 0.5, hero.position.y))
                
                break  # Only process one waypoint per frame
            
            # Check if reached final target
            if not path or len(path) == 0:
                final_distance = ((hero.position.x - target.position.x) ** 2 + 
                                (hero.position.y - target.position.y) ** 2) ** 0.5
                
                if final_distance <= target.follow_distance:
                    # Reached target
                    del self.hero_targets[hero_id]
                    if hero_id in self.hero_paths:
                        del self.hero_paths[hero_id]
                    logger.debug(f"Hero {hero_id} reached target")
                else:
                    # Recalculate path if not reached target but no path
                    self._calculate_path_to_target(hero_id, hero, target)
            
            self.state_changed = True
            # Update vision when hero moves
            self._update_vision(hero.player_id)
    
    def _get_target_position(self, target: MovementTarget) -> Optional[Position]:
        """Get current position of a dynamic target"""
        if target.target_type == TargetType.HERO and target.target_id:
            hero = self.game_state.heroes.get(target.target_id)
            return hero.position if hero else None
        elif target.target_type == TargetType.BUILDING and target.target_id:
            building = self.game_state.buildings.get(target.target_id)
            if building and building.health > 0:
                # Return position near building edge for interaction
                return Position(
                    x=building.position.x + building.size[0] / 2,
                    y=building.position.y + building.size[1] / 2
                )
            return None
        elif target.target_type == TargetType.ENEMY and target.target_id:
            enemy = self.game_state.enemies.get(target.target_id)
            return enemy.position if enemy and enemy.health > 0 else None
        elif target.target_type == TargetType.UNIT and target.target_id:
            unit = self.game_state.units.get(target.target_id)
            return unit.position if unit and unit.health > 0 else None
        else:
            return target.position
    
    def _calculate_path_to_target(self, hero_id: str, hero: Hero, target: MovementTarget):
        """Calculate path from hero to target using pathfinding"""
        target_pos = target.position
        
        # Adjust target position to account for follow distance
        if target.follow_distance > 0 and target.target_type != TargetType.POSITION:
            # For buildings, get to the edge plus follow distance
            if target.target_type == TargetType.BUILDING and target.target_id:
                building = self.game_state.buildings.get(target.target_id)
                if building:
                    # Find nearest edge of building
                    building_x = building.position.x
                    building_y = building.position.y
                    width, height = building.size
                    
                    # Calculate which edge is closest
                    hero_x, hero_y = hero.position.x, hero.position.y
                    
                    # Find closest point on building perimeter
                    closest_x = max(building_x, min(hero_x, building_x + width))
                    closest_y = max(building_y, min(hero_y, building_y + height))
                    
                    # Move away from building by follow distance
                    dx = hero_x - closest_x
                    dy = hero_y - closest_y
                    dist = (dx*dx + dy*dy)**0.5
                    
                    if dist > 0:
                        dx /= dist
                        dy /= dist
                        target_pos = Position(
                            x=closest_x + dx * target.follow_distance,
                            y=closest_y + dy * target.follow_distance
                        )
        
        # Find path
        path = self.pathfinder.find_path(
            hero.position.x, hero.position.y,
            target_pos.x, target_pos.y,
            self.game_state, hero_id
        )
        
        if path:
            self.hero_paths[hero_id] = path
            logger.debug(f"Calculated path for hero {hero_id} with {len(path)} waypoints")
        else:
            logger.debug(f"No path found for hero {hero_id} to target")
            # Remove target if no path possible
            if hero_id in self.hero_paths:
                del self.hero_paths[hero_id]
    
    def _is_dynamic_obstacle_at(self, x: float, y: float, excluding_hero_id: str = None) -> bool:
        """Check for dynamic obstacles (other heroes, enemies) - for pathfinding recalculation"""
        collision_radius = 0.4
        
        # Check other heroes
        for hero_id, hero in self.game_state.heroes.items():
            if hero_id == excluding_hero_id:
                continue
            dx = abs(hero.position.x - x)
            dy = abs(hero.position.y - y)
            if dx < collision_radius and dy < collision_radius:
                return True
        
        # Check enemies
        for enemy in self.game_state.enemies.values():
            if enemy.health <= 0:
                continue
            dx = abs(enemy.position.x - x)
            dy = abs(enemy.position.y - y)
            if dx < collision_radius and dy < collision_radius:
                return True
        
        return False
    
    def _is_position_blocked(self, x: float, y: float, excluding_hero_id: str = None) -> bool:
        """Check if a position is blocked by any collision"""
        # Convert to integer tile coordinates
        tile_x = int(x)
        tile_y = int(y)
        
        # Check map bounds
        if tile_x < 0 or tile_x >= MAP_WIDTH or tile_y < 0 or tile_y >= MAP_HEIGHT:
            return True
        
        # Check tile collision (trees and walls)
        if self._is_tile_collidable(tile_x, tile_y):
            return True
        
        # Check building collision
        if self._is_building_at_position(x, y):
            return True
        
        # Check hero collision
        if self._is_hero_at_position(x, y, excluding_hero_id):
            return True
        
        # Check enemy collision
        if self._is_enemy_at_position(x, y):
            return True
        
        return False
    
    def _is_tile_collidable(self, tile_x: int, tile_y: int) -> bool:
        """Check if a tile type is collidable"""
        from shared.models.game_models import TileType
        
        if tile_x < 0 or tile_x >= len(self.game_state.map_data[0]) or tile_y < 0 or tile_y >= len(self.game_state.map_data):
            return True
        
        tile_type = self.game_state.map_data[tile_y][tile_x]
        # WOOD tiles (trees) and WALL tiles are collidable
        return tile_type in [TileType.WOOD, TileType.WALL]
    
    def _is_building_at_position(self, x: float, y: float) -> bool:
        """Check if there's a building at the given position"""
        hero_radius = 0.4  # Heroes have a collision radius
        
        for building in self.game_state.buildings.values():
            if building.health <= 0:  # Skip destroyed buildings
                continue
            
            # Check if hero's collision area overlaps with building
            building_x = building.position.x
            building_y = building.position.y
            width, height = building.size
            
            # Expand building bounds by hero radius for proper collision
            if (building_x - hero_radius <= x <= building_x + width + hero_radius and 
                building_y - hero_radius <= y <= building_y + height + hero_radius):
                return True
        
        return False
    
    def _is_hero_at_position(self, x: float, y: float, excluding_hero_id: str = None) -> bool:
        """Check if there's another hero at the given position"""
        collision_radius = 0.4  # Heroes occupy roughly a 0.8x0.8 area
        
        for hero_id, hero in self.game_state.heroes.items():
            if hero_id == excluding_hero_id:  # Don't collide with self
                continue
            
            # Check distance between positions
            dx = abs(hero.position.x - x)
            dy = abs(hero.position.y - y)
            
            if dx < collision_radius and dy < collision_radius:
                return True
        
        return False
    
    def _is_enemy_at_position(self, x: float, y: float) -> bool:
        """Check if there's an enemy at the given position"""
        collision_radius = 0.4  # Enemies occupy roughly a 0.8x0.8 area
        
        for enemy in self.game_state.enemies.values():
            if enemy.health <= 0:  # Skip dead enemies
                continue
            
            # Check distance between positions
            dx = abs(enemy.position.x - x)
            dy = abs(enemy.position.y - y)
            
            if dx < collision_radius and dy < collision_radius:
                return True
        
        return False
    
    def _update_resources(self):
        for player_id, player in self.game_state.players.items():
            resource_income = Resources()
            
            for building in self.game_state.buildings.values():
                if building.player_id == player_id and building.health > 0:
                    income = self._calculate_building_income(building)
                    resource_income.wood += income.wood
                    resource_income.stone += income.stone
                    resource_income.wheat += income.wheat
                    resource_income.metal += income.metal
                    resource_income.gold += income.gold
            
            player.resources.wood += resource_income.wood
            player.resources.stone += resource_income.stone
            player.resources.wheat += resource_income.wheat
            player.resources.metal += resource_income.metal
            player.resources.gold += resource_income.gold
    
    def _calculate_building_income(self, building: Building) -> Resources:
        income = Resources()
        
        if building.building_type == BuildingType.FARM:
            if self._has_nearby_resource(building.position, TileType.WHEAT):
                income.wheat = 2
        elif building.building_type == BuildingType.WOOD_CUTTER:
            if self._has_nearby_resource(building.position, TileType.WOOD):
                income.wood = 3
        elif building.building_type == BuildingType.MINE:
            if self._has_nearby_resource(building.position, TileType.STONE):
                income.stone = 2
            elif self._has_nearby_resource(building.position, TileType.METAL):
                income.metal = 1
        elif building.building_type == BuildingType.GOLD_MINE:
            if self._has_nearby_resource(building.position, TileType.GOLD):
                income.gold = 1
        
        return income
    
    def _has_nearby_resource(self, position: Position, resource_type: TileType) -> bool:
        for dx in range(-2, 3):
            for dy in range(-2, 3):
                x, y = position.x + dx, position.y + dy
                if (0 <= x < MAP_WIDTH and 0 <= y < MAP_HEIGHT and
                    self.game_state.map_data[y][x] == resource_type):
                    return True
        return False
    
    def _spawn_enemy_wave(self):
        self.wave_number += 1
        enemies_per_corner = min(3 + self.wave_number // 2, 10)
        
        for corner in ENEMY_SPAWN_CORNERS:
            for _ in range(enemies_per_corner):
                enemy_id = str(uuid.uuid4())
                self.game_state.enemies[enemy_id] = Enemy(
                    id=enemy_id,
                    position=Position(x=corner[0], y=corner[1]),
                    health=30 + self.wave_number * 5,
                    max_health=30 + self.wave_number * 5,
                    target_position=Position(x=MAP_WIDTH//2, y=MAP_HEIGHT//2),
                    is_active=True
                )
    
    def _update_enemies(self):
        obstacles = self._get_obstacles()
        
        for enemy in self.game_state.enemies.values():
            if enemy.is_active and enemy.target_position:
                self._update_enemy_behavior(enemy, obstacles)
    
    def _update_enemy_behavior(self, enemy: Enemy, obstacles: List[Position]):
        if enemy.id not in self.enemy_paths:
            self._find_target_for_enemy(enemy)
        
        if enemy.id in self.enemy_paths and self.enemy_paths[enemy.id]:
            next_pos = self.enemy_paths[enemy.id][0]
            enemy.position = next_pos
            self.enemy_paths[enemy.id].pop(0)
            
            if not self.enemy_paths[enemy.id]:
                del self.enemy_paths[enemy.id]
        else:
            self._move_enemy_towards_target(enemy)
    
    def _find_target_for_enemy(self, enemy: Enemy):
        closest_target = None
        closest_distance = float('inf')
        
        for hero in self.game_state.heroes.values():
            if self._is_enemy_in_vision_range(enemy, hero.position):
                distance = self._distance(enemy.position.x, enemy.position.y, hero.position.x, hero.position.y)
                if distance < closest_distance:
                    closest_distance = distance
                    closest_target = hero.position
        
        for building in self.game_state.buildings.values():
            if building.player_id != "shared":
                if self._is_enemy_in_vision_range(enemy, building.position):
                    distance = self._distance(enemy.position.x, enemy.position.y, building.position.x, building.position.y)
                    if distance < closest_distance:
                        closest_distance = distance
                        closest_target = building.position
        
        if closest_target:
            enemy.target_position = closest_target
            obstacles = self._get_obstacles()
            path = self.pathfinding.find_path(enemy.position, enemy.target_position, obstacles)
            self.enemy_paths[enemy.id] = path
    
    def _is_enemy_in_vision_range(self, enemy: Enemy, target_pos: Position) -> bool:
        distance = self._distance(enemy.position.x, enemy.position.y, target_pos.x, target_pos.y)
        return distance <= 8
    
    def _get_obstacles(self) -> List[Position]:
        obstacles = []
        
        for building in self.game_state.buildings.values():
            for dx in range(building.size[0]):
                for dy in range(building.size[1]):
                    obstacles.append(Position(x=building.position.x + dx, y=building.position.y + dy))
        
        return obstacles
    
    def _distance(self, x1: int, y1: int, x2: int, y2: int) -> float:
        return ((x1 - x2) ** 2 + (y1 - y2) ** 2) ** 0.5
    
    def _move_enemy_towards_target(self, enemy: Enemy):
        if not enemy.target_position:
            return
            
        dx = enemy.target_position.x - enemy.position.x
        dy = enemy.target_position.y - enemy.position.y
        
        if abs(dx) > abs(dy):
            enemy.position.x += 1 if dx > 0 else -1
        elif dy != 0:
            enemy.position.y += 1 if dy > 0 else -1
        
        enemy.position.x = max(0, min(MAP_WIDTH - 1, enemy.position.x))
        enemy.position.y = max(0, min(MAP_HEIGHT - 1, enemy.position.y))
    
    def _update_vision(self, player_id: str):
        hero = self._get_player_hero(player_id)
        if hero:
            self._reveal_area(int(hero.position.x), int(hero.position.y), 5)
        
        for building in self.game_state.buildings.values():
            if building.player_id == player_id:
                self._reveal_area(int(building.position.x), int(building.position.y), 3)
    
    def _reveal_area(self, center_x: int, center_y: int, radius: int):
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                x, y = center_x + dx, center_y + dy
                if (0 <= x < MAP_WIDTH and 0 <= y < MAP_HEIGHT and
                    dx*dx + dy*dy <= radius*radius):
                    self.game_state.fog_of_war[y][x] = True
    
    def _get_player_hero(self, player_id: str) -> Optional[Hero]:
        for hero in self.game_state.heroes.values():
            if hero.player_id == player_id:
                return hero
        return None
    
    def _check_game_over(self):
        town_hall = None
        for building in self.game_state.buildings.values():
            if building.building_type == BuildingType.TOWN_HALL:
                town_hall = building
                break
        
        if town_hall and town_hall.health <= 0:
            self.game_state.is_active = False
    
    def get_game_state(self) -> GameState:
        return self.game_state
    
    def move_hero(self, player_id: str, target_position: Position) -> bool:
        hero = self._get_player_hero(player_id)
        if hero:
            # Create movement target for position
            target = MovementTarget(
                target_type=TargetType.POSITION,
                position=target_position,
                follow_distance=0.5
            )
            
            # Set movement target and calculate initial path
            self.hero_targets[hero.id] = target
            self._calculate_path_to_target(hero.id, hero, target)
            
            logger.debug(f"Hero {hero.id} targeting position {target_position.x}, {target_position.y}")
            self.state_changed = True
            return True
        return False
    
    def move_hero_to_target(self, player_id: str, target_type: TargetType, target_id: str = None, 
                           target_position: Position = None) -> bool:
        """Move hero to a specific target (building, enemy, unit, hero)"""
        hero = self._get_player_hero(player_id)
        if not hero:
            return False
        
        # Determine follow distance based on target type
        follow_distance = 1.0  # Default distance
        if target_type == TargetType.BUILDING:
            follow_distance = 1.5  # Stay a bit away from buildings
        elif target_type in [TargetType.ENEMY, TargetType.UNIT]:
            follow_distance = 1.0  # Close enough for combat/interaction
        elif target_type == TargetType.HERO:
            follow_distance = 0.8  # Close to other heroes
        
        # Get target position
        if target_position is None:
            if target_type == TargetType.BUILDING and target_id:
                building = self.game_state.buildings.get(target_id)
                if not building or building.health <= 0:
                    return False
                target_position = Position(
                    x=building.position.x + building.size[0] / 2,
                    y=building.position.y + building.size[1] / 2
                )
            elif target_type == TargetType.HERO and target_id:
                target_hero = self.game_state.heroes.get(target_id)
                if not target_hero:
                    return False
                target_position = target_hero.position
            elif target_type == TargetType.ENEMY and target_id:
                enemy = self.game_state.enemies.get(target_id)
                if not enemy or enemy.health <= 0:
                    return False
                target_position = enemy.position
            elif target_type == TargetType.UNIT and target_id:
                unit = self.game_state.units.get(target_id)
                if not unit or unit.health <= 0:
                    return False
                target_position = unit.position
            else:
                return False
        
        # Create movement target
        target = MovementTarget(
            target_type=target_type,
            position=target_position,
            target_id=target_id,
            follow_distance=follow_distance
        )
        
        # Set movement target and calculate initial path
        self.hero_targets[hero.id] = target
        self._calculate_path_to_target(hero.id, hero, target)
        
        logger.debug(f"Hero {hero.id} targeting {target_type.value} {target_id or 'position'}")
        self.state_changed = True
        return True
    
    def build_structure(self, player_id: str, building_type: BuildingType, position: Position) -> bool:
        player = self.game_state.players.get(player_id)
        if not player:
            return False
        
        building_info = BUILDING_TYPES.get(building_type)
        if not building_info:
            return False
        
        cost = building_info["cost"]
        if not self._can_afford(player, cost):
            return False
        
        if not self._is_valid_build_position(position, building_info["size"]):
            return False
        
        self._deduct_resources(player, cost)
        
        building_id = str(uuid.uuid4())
        self.game_state.buildings[building_id] = Building(
            id=building_id,
            building_type=building_type,
            position=position,
            health=building_info["health"],
            max_health=building_info["health"],
            player_id=player_id,
            size=building_info["size"]
        )
        
        return True
    
    def _can_afford(self, player: Player, cost: Dict[str, int]) -> bool:
        return all(getattr(player.resources, resource, 0) >= amount 
                  for resource, amount in cost.items())
    
    def _deduct_resources(self, player: Player, cost: Dict[str, int]):
        for resource, amount in cost.items():
            current = getattr(player.resources, resource, 0)
            setattr(player.resources, resource, max(0, current - amount))
    
    def _is_valid_build_position(self, position: Position, size: tuple) -> bool:
        width, height = size
        for dx in range(width):
            for dy in range(height):
                x, y = position.x + dx, position.y + dy
                if not (0 <= x < MAP_WIDTH and 0 <= y < MAP_HEIGHT):
                    return False
                
                for building in self.game_state.buildings.values():
                    if (building.position.x <= x < building.position.x + building.size[0] and
                        building.position.y <= y < building.position.y + building.size[1]):
                        return False
        
        return True
    
    def _cleanup_expired_pings(self, current_time: float):
        """Remove pings that have expired"""
        expired_pings = []
        for ping_id, ping in self.game_state.pings.items():
            if current_time - ping.timestamp >= ping.duration:
                expired_pings.append(ping_id)
        
        for ping_id in expired_pings:
            del self.game_state.pings[ping_id]
            if expired_pings:
                self.state_changed = True
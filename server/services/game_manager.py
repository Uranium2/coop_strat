import uuid
import time
import logging
from typing import Dict, List, Optional
from shared.models.game_models import (
    GameState, Player, Hero, Building, Unit, Enemy, Position, 
    HeroType, BuildingType, TileType, Resources
)
from shared.constants.game_constants import (
    MAP_WIDTH, MAP_HEIGHT, HERO_TYPES, BUILDING_TYPES, 
    RESOURCE_TICK_RATE, WAVE_SPAWN_INTERVAL, ENEMY_SPAWN_CORNERS
)
from server.services.map_generator import MapGenerator
from server.services.pathfinding import PathfindingService

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
        self.pathfinding = PathfindingService(MAP_WIDTH, MAP_HEIGHT)
        self.enemy_paths = {}
        
        # Movement and tick system
        self.hero_targets = {}  # Store movement targets for heroes
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
            self._check_game_over()
        
        # Return state only if something changed and enough time passed for network update
        if self.state_changed and (current_time - self.last_network_update >= 1.0 / self.network_update_rate):
            self.last_network_update = current_time
            self.state_changed = False
            return self.game_state
        
        return None
    
    def _update_hero_movements(self, dt: float):
        """Update hero positions based on their movement targets"""
        for hero_id, hero in self.game_state.heroes.items():
            if hero_id in self.hero_targets:
                target_pos = self.hero_targets[hero_id]
                hero_stats = HERO_TYPES[hero.hero_type.value]
                speed = hero_stats["speed"]  # tiles per second
                
                # Calculate direction to target
                dx = target_pos.x - hero.position.x
                dy = target_pos.y - hero.position.y
                distance = (dx * dx + dy * dy) ** 0.5
                
                if distance > 0.1:  # Still moving towards target
                    # Normalize direction and apply speed
                    move_distance = speed * dt
                    if move_distance >= distance:
                        # Reached target
                        hero.position.x = target_pos.x
                        hero.position.y = target_pos.y
                        del self.hero_targets[hero_id]
                        logger.debug(f"Hero {hero_id} reached target {target_pos.x}, {target_pos.y}")
                    else:
                        # Move towards target
                        move_x = (dx / distance) * move_distance
                        move_y = (dy / distance) * move_distance
                        hero.position.x += move_x
                        hero.position.y += move_y
                        
                        # Ensure hero stays within map bounds
                        hero.position.x = max(0, min(MAP_WIDTH - 1, hero.position.x))
                        hero.position.y = max(0, min(MAP_HEIGHT - 1, hero.position.y))
                    
                    self.state_changed = True
                    # Update vision when hero moves
                    self._update_vision(hero.player_id)
                else:
                    # Already at target
                    if hero_id in self.hero_targets:
                        del self.hero_targets[hero_id]
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
            # Set movement target instead of teleporting
            self.hero_targets[hero.id] = target_position
            logger.debug(f"Hero {hero.id} targeting position {target_position.x}, {target_position.y}")
            self.state_changed = True
            return True
        return False
    
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
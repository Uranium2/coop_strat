import logging
import random
import time
import uuid
from typing import Dict, List, Optional

from server.services.combat_service import CombatService
from server.services.map_generator import MapGenerator
from server.services.pathfinding import Pathfinder
from shared.constants.game_constants import (
    BUILDING_TYPES,
    ENEMY_SPAWN_CORNERS,
    ENEMY_TYPES,
    FIRST_WAVE_DELAY,
    HERO_TYPES,
    MAP_HEIGHT,
    MAP_WIDTH,
    RESOURCE_TICK_RATE,
    WAVE_SPAWN_INTERVAL,
)
from shared.models.game_models import (
    Building,
    BuildingType,
    Enemy,
    GameOverReason,
    GameState,
    Hero,
    MovementTarget,
    Player,
    Position,
    Resources,
    TargetType,
    TileType,
)

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
            is_active=True,
        )

        self.last_resource_tick = time.time()
        self.last_wave_spawn = time.time()  # Track when last wave was spawned
        self.wave_number = 0
        self.pathfinder = Pathfinder(MAP_WIDTH, MAP_HEIGHT)
        self.enemy_paths = {}
        self.combat_service = CombatService()

        # Movement and tick system
        self.hero_targets: Dict[
            str, MovementTarget
        ] = {}  # Store movement targets for heroes
        self.hero_paths: Dict[
            str, List[Position]
        ] = {}  # Store current paths for heroes
        self.last_update = time.time()
        self.tick_rate = 60  # 60 FPS server tick rate
        self.network_update_rate = 20  # Send updates to clients 20 times per second
        self.last_network_update = time.time()
        self.state_changed = False

        self._initialize_game()

    def _initialize_game(self):
        # Use lobby_id hash as seed to ensure all players get the same map
        seed = hash(self.lobby_id) % (2**32)
        logger.info(
            f"Initializing game for lobby {self.lobby_id} with map seed: {seed}"
        )

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
            size=(3, 3),
        )

        hero_positions = [
            (center_x - 2, center_y - 2),
            (center_x + 2, center_y - 2),
            (center_x - 2, center_y + 2),
            (center_x + 2, center_y + 2),
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
                    max_health=hero_stats["health"],
                    attack_damage=hero_stats["attack_damage"],
                    attack_range=hero_stats["attack_range"],
                    speed=hero_stats["speed"],
                    attack_speed=hero_stats["attack_speed"],
                )

        # Initialize shared fog of war for all players
        self.game_state.fog_of_war = [
            [False for _ in range(MAP_WIDTH)] for _ in range(MAP_HEIGHT)
        ]

        # Initialize wave timer - first wave spawns after FIRST_WAVE_DELAY
        current_time = time.time()
        self.game_state.wave_number = 0
        self.game_state.next_wave_time = current_time + FIRST_WAVE_DELAY
        self.game_state.time_to_next_wave = FIRST_WAVE_DELAY

        # Update vision for all players initially
        for player_id in self.game_state.players:
            self._update_vision(player_id)

    def update(self) -> Optional[GameState]:
        current_time = time.time()
        dt = current_time - self.last_update
        self.last_update = current_time

        # Update game logic at 60 FPS - but only if not paused
        if dt >= 1.0 / self.tick_rate:
            # Always update game time for consistency, even when paused
            self.game_state.game_time += dt

            # Skip game logic updates if paused
            if not self.game_state.is_paused:
                # Update hero movements
                self._update_hero_movements(dt)

                # Resource updates every 2 seconds
                if current_time - self.last_resource_tick >= RESOURCE_TICK_RATE:
                    self._update_resources()
                    self.last_resource_tick = current_time
                    self.state_changed = True

                # Wave spawning system
                self._update_wave_timer(current_time)
                if current_time >= self.game_state.next_wave_time:
                    logger.info(
                        f"Wave spawn timer triggered. Current enemies: {len(self.game_state.enemies)}"
                    )
                    self._spawn_enemy_wave()
                    self._schedule_next_wave(current_time)
                    self.state_changed = True

                # TEMPORARY: Spawn single test enemy near hero - DISABLED
                # if current_time - self.last_wave_spawn >= WAVE_SPAWN_INTERVAL:
                #     self._spawn_test_enemy()
                #     self.last_wave_spawn = current_time
                #     self.state_changed = True

                # Update enemies
                self._update_enemies()

                # Process combat interactions
                self._process_combat()

                self._check_game_over()

            # Always clean up expired pings regardless of pause state
            self._cleanup_expired_pings(current_time)

            # Clean up expired attack effects
            self._cleanup_expired_attack_effects(current_time)

            # Clean up dead enemies after 20 seconds
            self._cleanup_dead_enemies(current_time)

        # Return state only if something changed and enough time passed for network update
        if self.state_changed and (
            current_time - self.last_network_update >= 1.0 / self.network_update_rate
        ):
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
                    if (
                        abs(new_target_pos.x - target.position.x) > 0.5
                        or abs(new_target_pos.y - target.position.y) > 0.5
                    ):
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
                final_distance = (
                    (hero.position.x - target.position.x) ** 2
                    + (hero.position.y - target.position.y) ** 2
                ) ** 0.5

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
                    y=building.position.y + building.size[1] / 2,
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

    def _calculate_path_to_target(
        self, hero_id: str, hero: Hero, target: MovementTarget
    ):
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
                    dist = (dx * dx + dy * dy) ** 0.5

                    if dist > 0:
                        dx /= dist
                        dy /= dist
                        target_pos = Position(
                            x=closest_x + dx * target.follow_distance,
                            y=closest_y + dy * target.follow_distance,
                        )

        # Find path
        path = self.pathfinder.find_path(
            hero.position.x,
            hero.position.y,
            target_pos.x,
            target_pos.y,
            self.game_state,
            hero_id,
        )

        if path:
            self.hero_paths[hero_id] = path
            logger.debug(
                f"Calculated path for hero {hero_id} with {len(path)} waypoints"
            )
        else:
            logger.debug(f"No path found for hero {hero_id} to target")
            # Remove target if no path possible
            if hero_id in self.hero_paths:
                del self.hero_paths[hero_id]

    def _is_dynamic_obstacle_at(
        self, x: float, y: float, excluding_hero_id: str = None
    ) -> bool:
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

    def _is_position_blocked(
        self, x: float, y: float, excluding_hero_id: str = None
    ) -> bool:
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

        if (
            tile_x < 0
            or tile_x >= len(self.game_state.map_data[0])
            or tile_y < 0
            or tile_y >= len(self.game_state.map_data)
        ):
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
            if (
                building_x - hero_radius <= x <= building_x + width + hero_radius
                and building_y - hero_radius <= y <= building_y + height + hero_radius
            ):
                return True

        return False

    def _is_hero_at_position(
        self, x: float, y: float, excluding_hero_id: str = None
    ) -> bool:
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
                if (
                    0 <= x < MAP_WIDTH
                    and 0 <= y < MAP_HEIGHT
                    and self.game_state.map_data[y][x] == resource_type
                ):
                    return True
        return False

    def _update_wave_timer(self, current_time: float):
        """Update the wave timer countdown"""
        self.game_state.time_to_next_wave = max(
            0, self.game_state.next_wave_time - current_time
        )

        # Update state if timer changed significantly (every second)
        if int(self.game_state.time_to_next_wave) != int(
            getattr(self, "_last_timer_update", 0)
        ):
            self.state_changed = True
            self._last_timer_update = self.game_state.time_to_next_wave

    def _schedule_next_wave(self, current_time: float):
        """Schedule the next wave spawn"""
        self.game_state.next_wave_time = current_time + WAVE_SPAWN_INTERVAL
        self.game_state.time_to_next_wave = WAVE_SPAWN_INTERVAL

    def _spawn_enemy_wave(self):
        self.wave_number += 1
        self.game_state.wave_number = self.wave_number
        enemies_per_corner = min(
            1 + self.wave_number // 3, 4
        )  # Start with 1, scale slowly

        logger.info(
            f"Spawning wave {self.wave_number} with {enemies_per_corner} enemies per corner"
        )

        # Find the actual town hall position
        town_hall = self._find_town_hall()
        if town_hall:
            town_hall_target = Position(
                x=town_hall.position.x + town_hall.size[0] / 2,
                y=town_hall.position.y + town_hall.size[1] / 2,
            )
        else:
            # Fallback to map center if no town hall found
            town_hall_target = Position(x=MAP_WIDTH // 2, y=MAP_HEIGHT // 2)

        for corner in ENEMY_SPAWN_CORNERS:
            for _ in range(enemies_per_corner):
                enemy_id = str(uuid.uuid4())

                # Choose enemy type based on wave number
                if self.wave_number <= 2:
                    enemy_type = "BASIC"
                elif self.wave_number <= 4:
                    enemy_type = "FAST" if random.random() < 0.3 else "BASIC"
                elif self.wave_number <= 6:
                    enemy_type = random.choice(["BASIC", "FAST", "RANGED"])
                else:
                    enemy_type = random.choice(["BASIC", "FAST", "RANGED", "HEAVY"])

                enemy_stats = ENEMY_TYPES[enemy_type]

                # Scale health with wave number
                health_scaling = self.wave_number * 3  # Less aggressive scaling
                scaled_health = enemy_stats["health"] + health_scaling

                # Add small random offset to prevent enemies from spawning at identical positions
                spawn_x = corner[0] + random.uniform(-1, 1)
                spawn_y = corner[1] + random.uniform(-1, 1)

                self.game_state.enemies[enemy_id] = Enemy(
                    id=enemy_id,
                    position=Position(x=spawn_x, y=spawn_y),
                    health=scaled_health,
                    max_health=scaled_health,
                    target_position=town_hall_target,  # Target actual town hall
                    is_active=True,
                    attack_damage=enemy_stats["attack_damage"],
                    attack_range=enemy_stats["attack_range"],
                    speed=enemy_stats["speed"],
                    attack_speed=enemy_stats["attack_speed"],
                )

        logger.info(
            f"Wave {self.wave_number} spawned: {len(ENEMY_SPAWN_CORNERS) * enemies_per_corner} total enemies targeting town hall at ({town_hall_target.x}, {town_hall_target.y})"
        )

    def _spawn_test_enemy(self):
        """TEMPORARY: Spawn a single enemy near the first hero for combat testing"""
        # Only spawn if we don't already have test enemies
        if len(self.game_state.enemies) > 0:
            return

        # Find the first hero
        if not self.game_state.heroes:
            return

        first_hero = list(self.game_state.heroes.values())[0]

        # Spawn enemy 3 units away from hero
        enemy_id = str(uuid.uuid4())
        enemy_stats = ENEMY_TYPES["BASIC"]
        enemy_x = first_hero.position.x + 3
        enemy_y = first_hero.position.y + 1

        self.game_state.enemies[enemy_id] = Enemy(
            id=enemy_id,
            position=Position(x=enemy_x, y=enemy_y),
            health=enemy_stats["health"],
            max_health=enemy_stats["health"],
            target_position=None,  # No target - don't move
            is_active=True,
            attack_damage=enemy_stats["attack_damage"],
            attack_range=enemy_stats["attack_range"],
            speed=enemy_stats["speed"],
            attack_speed=enemy_stats["attack_speed"],
        )

        # logger.info(f"Spawned test enemy at ({enemy_x}, {enemy_y}) near hero at ({first_hero.position.x}, {first_hero.position.y})")

    def _update_enemies(self):
        """Update enemy AI behavior - target town hall and attack obstacles"""
        dt = 1.0 / self.tick_rate  # Time delta for movement calculations

        if self.game_state.enemies:
            logger.debug(f"Updating {len(self.game_state.enemies)} enemies")

        for enemy in self.game_state.enemies.values():
            if not enemy.is_active or enemy.health <= 0 or enemy.is_dead:
                logger.debug(
                    f"Enemy {enemy.id} skipped - active:{enemy.is_active}, health:{enemy.health}, dead:{enemy.is_dead}"
                )
                continue

            # Set target to town hall if not set or target is gone
            if not enemy.target_position:
                town_hall = self._find_town_hall()
                if town_hall:
                    enemy.target_position = Position(
                        x=town_hall.position.x + town_hall.size[0] / 2,
                        y=town_hall.position.y + town_hall.size[1] / 2,
                    )
                else:
                    logger.warning(
                        f"No town hall found for enemy {enemy.id} to target!"
                    )

            if enemy.target_position:
                old_pos = (enemy.position.x, enemy.position.y)
                self._update_enemy_behavior(enemy, dt)
                new_pos = (enemy.position.x, enemy.position.y)
                if old_pos != new_pos:
                    pass

        # Mark state as changed if any enemies moved/acted
        if self.game_state.enemies:
            self.state_changed = True

    def _update_enemy_behavior(self, enemy: Enemy, dt: float):
        """Update individual enemy behavior - move toward target and attack anything in range"""

        # First check if there's any player unit or building to attack
        target_to_attack = self._find_target_to_attack(enemy)

        if target_to_attack:
            # Attack the target instead of moving
            self._enemy_attack_target(enemy, target_to_attack)
        else:
            # Move toward target (town hall)
            self._move_enemy_towards_target(enemy, dt)

    def _find_target_to_attack(self, enemy: Enemy):
        """Find any player unit or building within attack range"""
        targets = []

        # Check all player buildings (not just blocking ones)
        for building in self.game_state.buildings.values():
            if building.health <= 0:
                continue

            # Skip shared buildings (like town hall) initially - attack player buildings first
            if building.player_id == "shared":
                continue

            # Calculate distance to building center
            building_center_x = building.position.x + building.size[0] / 2
            building_center_y = building.position.y + building.size[1] / 2

            distance = self._distance(
                enemy.position.x, enemy.position.y, building_center_x, building_center_y
            )

            # Check if building is within attack range (accounting for building size)
            effective_range = enemy.attack_range + max(building.size) / 2
            if distance <= effective_range:
                targets.append(("building", building, distance))

        # Check all player heroes
        for hero in self.game_state.heroes.values():
            if hero.health <= 0:
                continue

            distance = self._distance(
                enemy.position.x, enemy.position.y, hero.position.x, hero.position.y
            )

            if distance <= enemy.attack_range:
                targets.append(("hero", hero, distance))

        # Check all player units
        for unit in self.game_state.units.values():
            if unit.health <= 0:
                continue

            distance = self._distance(
                enemy.position.x, enemy.position.y, unit.position.x, unit.position.y
            )

            if distance <= enemy.attack_range:
                targets.append(("unit", unit, distance))

        # Attack the closest target
        if targets:
            targets.sort(key=lambda x: x[2])  # Sort by distance
            return targets[0]  # Return closest target

        # If no other targets, check town hall (shared buildings)
        for building in self.game_state.buildings.values():
            if building.health <= 0:
                continue

            if building.player_id == "shared":  # Town hall and other shared buildings
                building_center_x = building.position.x + building.size[0] / 2
                building_center_y = building.position.y + building.size[1] / 2

                distance = self._distance(
                    enemy.position.x,
                    enemy.position.y,
                    building_center_x,
                    building_center_y,
                )

                effective_range = enemy.attack_range + max(building.size) / 2
                if distance <= effective_range:
                    return ("building", building, distance)

        return None

    def _enemy_attack_target(self, enemy: Enemy, target_info):
        """Make enemy attack any target (building, hero, or unit)"""
        target_type, target, distance = target_info

        if target_type == "building":
            self._enemy_attack_building(enemy, target)
        elif target_type == "hero":
            self._enemy_attack_hero(enemy, target)
        elif target_type == "unit":
            self._enemy_attack_unit(enemy, target)

    def _enemy_attack_building(self, enemy: Enemy, building: Building):
        """Make enemy attack a building"""
        # Apply damage to the building
        building.health = max(0, building.health - enemy.attack_damage)

        # Create attack effect for visual feedback
        attack_effect = self.combat_service.create_attack_effect(
            attacker_id=enemy.id,
            target_id=building.id,
            attacker_pos=enemy.position,
            target_pos=Position(
                x=building.position.x + building.size[0] / 2,
                y=building.position.y + building.size[1] / 2,
            ),
            damage=int(enemy.attack_damage),
            effect_type="MELEE",  # Most enemies are melee
        )

        self.game_state.attack_effects[attack_effect.id] = attack_effect
        self.state_changed = True

        # logger.info(
        #     f"Enemy {enemy.id} attacked building {building.building_type.value} for {enemy.attack_damage} damage. Building health: {building.health}"
        # )

        # If building is destroyed, log it
        if building.health <= 0:
            logger.info(f"Building {building.building_type.value} destroyed by enemy!")

    def _enemy_attack_hero(self, enemy: Enemy, hero: Hero):
        """Make enemy attack a hero"""
        # Apply damage to the hero
        hero.health -= enemy.attack_damage

        # Create attack effect for visual feedback
        attack_effect = self.combat_service.create_attack_effect(
            attacker_id=enemy.id,
            target_id=hero.id,
            attacker_pos=enemy.position,
            target_pos=hero.position,
            damage=int(enemy.attack_damage),
            effect_type="MELEE",
        )

        self.game_state.attack_effects[attack_effect.id] = attack_effect
        self.state_changed = True

        if hero.health <= 0:
            logger.info(f"Hero {hero.hero_type.value} killed by enemy!")

    def _enemy_attack_unit(self, enemy: Enemy, unit):
        """Make enemy attack a unit"""
        # Apply damage to the unit
        unit.health -= enemy.attack_damage

        # Create attack effect for visual feedback
        attack_effect = self.combat_service.create_attack_effect(
            attacker_id=enemy.id,
            target_id=unit.id,
            attacker_pos=enemy.position,
            target_pos=unit.position,
            damage=int(enemy.attack_damage),
            effect_type="MELEE",
        )

        self.game_state.attack_effects[attack_effect.id] = attack_effect
        self.state_changed = True

        if unit.health <= 0:
            logger.info(f"Unit {unit.unit_type.value} killed by enemy!")

    def _find_town_hall(self) -> Optional[Building]:
        """Find the town hall building"""
        for building in self.game_state.buildings.values():
            if building.building_type == BuildingType.TOWN_HALL and building.health > 0:
                return building
        return None

    def _find_target_for_enemy(self, enemy: Enemy):
        closest_target = None
        closest_distance = float("inf")

        for hero in self.game_state.heroes.values():
            if self._is_enemy_in_vision_range(enemy, hero.position):
                distance = self._distance(
                    enemy.position.x, enemy.position.y, hero.position.x, hero.position.y
                )
                if distance < closest_distance:
                    closest_distance = distance
                    closest_target = hero.position

        for building in self.game_state.buildings.values():
            if building.player_id != "shared":
                if self._is_enemy_in_vision_range(enemy, building.position):
                    distance = self._distance(
                        enemy.position.x,
                        enemy.position.y,
                        building.position.x,
                        building.position.y,
                    )
                    if distance < closest_distance:
                        closest_distance = distance
                        closest_target = building.position

        if closest_target:
            enemy.target_position = closest_target
            obstacles = self._get_obstacles()
            path = self.pathfinder.find_path(
                enemy.position.x,
                enemy.position.y,
                enemy.target_position.x,
                enemy.target_position.y,
                self.game_state,
            )
            self.enemy_paths[enemy.id] = path

    def _is_enemy_in_vision_range(self, enemy: Enemy, target_pos: Position) -> bool:
        distance = self._distance(
            enemy.position.x, enemy.position.y, target_pos.x, target_pos.y
        )
        return distance <= 8

    def _get_obstacles(self) -> List[Position]:
        obstacles = []

        for building in self.game_state.buildings.values():
            for dx in range(building.size[0]):
                for dy in range(building.size[1]):
                    obstacles.append(
                        Position(x=building.position.x + dx, y=building.position.y + dy)
                    )

        return obstacles

    def _distance(self, x1: int, y1: int, x2: int, y2: int) -> float:
        return ((x1 - x2) ** 2 + (y1 - y2) ** 2) ** 0.5

    def _move_enemy_towards_target(self, enemy: Enemy, dt: float):
        """Move enemy toward their target position"""
        if not enemy.target_position:
            return

        # Calculate direction to target
        dx = enemy.target_position.x - enemy.position.x
        dy = enemy.target_position.y - enemy.position.y
        distance = (dx * dx + dy * dy) ** 0.5

        # Move toward target
        move_distance = enemy.speed * dt

        if move_distance >= distance:
            # Reached target this frame
            enemy.position.x = enemy.target_position.x
            enemy.position.y = enemy.target_position.y
            self.state_changed = True
        else:
            # Move toward target
            move_x = (dx / distance) * move_distance
            move_y = (dy / distance) * move_distance

            new_x = enemy.position.x + move_x
            new_y = enemy.position.y + move_y

            # Check for collisions with other enemies - use smaller collision radius for easier movement
            collision = False
            collision_radius = 0.2  # Reduced from 0.4 to allow easier movement
            for other_enemy in self.game_state.enemies.values():
                if other_enemy.id == enemy.id or other_enemy.health <= 0:
                    continue
                dx_other = abs(other_enemy.position.x - new_x)
                dy_other = abs(other_enemy.position.y - new_y)
                if dx_other < collision_radius and dy_other < collision_radius:
                    collision = True
                    break

            if not collision:
                enemy.position.x = new_x
                enemy.position.y = new_y
                self.state_changed = True
            else:
                # Simple collision avoidance - just move with a small random offset
                random_offset_x = random.uniform(-0.5, 0.5)
                random_offset_y = random.uniform(-0.5, 0.5)

                new_x_offset = enemy.position.x + move_x + random_offset_x
                new_y_offset = enemy.position.y + move_y + random_offset_y

                # Apply the movement even with collision - enemies can push through
                enemy.position.x = new_x_offset
                enemy.position.y = new_y_offset
                self.state_changed = True

        # Ensure enemy stays within map bounds
        enemy.position.x = max(0.5, min(MAP_WIDTH - 0.5, enemy.position.x))
        enemy.position.y = max(0.5, min(MAP_HEIGHT - 0.5, enemy.position.y))

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
                if (
                    0 <= x < MAP_WIDTH
                    and 0 <= y < MAP_HEIGHT
                    and dx * dx + dy * dy <= radius * radius
                ):
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
            self.game_state.game_over_reason = GameOverReason.TOWN_HALL_DESTROYED
            logger.info("Game Over: Town Hall destroyed!")
            self.state_changed = True

    def get_game_state(self) -> GameState:
        return self.game_state

    def move_hero(self, player_id: str, target_position: Position) -> bool:
        hero = self._get_player_hero(player_id)
        if hero:
            # Create movement target for position
            target = MovementTarget(
                target_type=TargetType.POSITION,
                position=target_position,
                follow_distance=0.5,
            )

            # Set movement target and calculate initial path
            self.hero_targets[hero.id] = target
            self._calculate_path_to_target(hero.id, hero, target)

            logger.debug(
                f"Hero {hero.id} targeting position {target_position.x}, {target_position.y}"
            )
            self.state_changed = True
            return True
        return False

    def move_hero_to_target(
        self,
        player_id: str,
        target_type: TargetType,
        target_id: str = None,
        target_position: Position = None,
    ) -> bool:
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
                    y=building.position.y + building.size[1] / 2,
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
            follow_distance=follow_distance,
        )

        # Set movement target and calculate initial path
        self.hero_targets[hero.id] = target
        self._calculate_path_to_target(hero.id, hero, target)

        logger.debug(
            f"Hero {hero.id} targeting {target_type.value} {target_id or 'position'}"
        )
        self.state_changed = True
        return True

    def build_structure(
        self, player_id: str, building_type: BuildingType, position: Position
    ) -> bool:
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
            size=building_info["size"],
        )

        return True

    def _can_afford(self, player: Player, cost: Dict[str, int]) -> bool:
        return all(
            getattr(player.resources, resource, 0) >= amount
            for resource, amount in cost.items()
        )

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
                    if (
                        building.position.x
                        <= x
                        < building.position.x + building.size[0]
                        and building.position.y
                        <= y
                        < building.position.y + building.size[1]
                    ):
                        return False

        return True

    def _process_combat(self):
        """Process combat interactions between heroes and enemies, and enemies and buildings"""

        # Check each hero against each enemy
        for hero in self.game_state.heroes.values():
            if hero.health <= 0:
                continue

            for enemy in self.game_state.enemies.values():
                if enemy.health <= 0 or enemy.is_dead:
                    continue

                # Calculate distance between hero and enemy
                distance = self._distance(
                    hero.position.x, hero.position.y, enemy.position.x, enemy.position.y
                )

                # Debug logging
                # logger.debug(f"Hero at ({hero.position.x}, {hero.position.y}) vs Enemy at ({enemy.position.x}, {enemy.position.y}), distance: {distance}")

                # Check if hero can attack enemy (use hero's attack range)
                if distance <= hero.attack_range:
                    # logger.info(f"Hero attacks! Hero range: {hero.attack_range}, distance: {distance}")
                    # Hero attacks enemy
                    enemy_died, attack_effect = self.combat_service.apply_damage(
                        hero, enemy
                    )
                    self.game_state.attack_effects[attack_effect.id] = attack_effect
                    if enemy_died:
                        enemy.health = 0
                        enemy.is_dead = True
                        enemy.death_time = time.time()  # Record death timestamp
                        self.state_changed = True
                        logger.info("Enemy died!")

                # Check if enemy can attack hero back (use enemy's attack range, only if enemy is alive)
                if not enemy.is_dead and distance <= enemy.attack_range:
                    logger.info(
                        f"Enemy attacks back! Enemy range: {enemy.attack_range}, distance: {distance}"
                    )
                    hero_died, counter_attack_effect = self.combat_service.apply_damage(
                        enemy, hero
                    )
                    self.game_state.attack_effects[counter_attack_effect.id] = (
                        counter_attack_effect
                    )
                    if hero_died:
                        hero.health = 0
                        self.state_changed = True
                        logger.info("Hero died!")

        # Check enemies attacking buildings (in addition to the movement-based attacks)
        for enemy in self.game_state.enemies.values():
            if enemy.health <= 0 or enemy.is_dead:
                continue

            # Check if enemy can attack any building
            for building in self.game_state.buildings.values():
                if building.health <= 0:
                    continue

                # Calculate distance to building
                building_center_x = building.position.x + building.size[0] / 2
                building_center_y = building.position.y + building.size[1] / 2

                distance = self._distance(
                    enemy.position.x,
                    enemy.position.y,
                    building_center_x,
                    building_center_y,
                )

                # Account for building size when checking range
                effective_range = enemy.attack_range + max(building.size) / 2

                if distance <= effective_range:
                    # Enemy can attack building - this is handled in movement logic
                    # to avoid double-attacking, but we log it for debugging
                    break

    def _cleanup_expired_attack_effects(self, current_time: float):
        """Remove attack effects that have finished their animation"""
        expired_effects = []
        for effect_id, effect in self.game_state.attack_effects.items():
            if current_time - effect.start_time >= effect.duration:
                expired_effects.append(effect_id)

        for effect_id in expired_effects:
            del self.game_state.attack_effects[effect_id]

        if expired_effects:
            self.state_changed = True

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

    def _cleanup_dead_enemies(self, current_time: float):
        """Remove enemies that have been dead for more than 20 seconds"""
        DEATH_CLEANUP_TIME = 20.0  # 20 seconds

        expired_enemies = []
        for enemy_id, enemy in self.game_state.enemies.items():
            if enemy.is_dead and enemy.death_time:
                time_since_death = current_time - enemy.death_time
                if time_since_death >= DEATH_CLEANUP_TIME:
                    expired_enemies.append(enemy_id)

        for enemy_id in expired_enemies:
            del self.game_state.enemies[enemy_id]
            logger.info(
                f"Removed dead enemy {enemy_id} after {DEATH_CLEANUP_TIME} seconds"
            )

        if expired_enemies:
            self.state_changed = True

    def toggle_pause(self) -> bool:
        """Toggle the pause state of the game"""
        try:
            self.game_state.is_paused = not self.game_state.is_paused
            self.state_changed = True
            logger.info(f"Game pause toggled to: {self.game_state.is_paused}")
            return True
        except Exception as e:
            logger.error(f"Failed to toggle pause: {e}")
            return False

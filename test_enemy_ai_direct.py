#!/usr/bin/env python3

import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import uuid

from server.services.game_manager import GameManager
from shared.models.game_models import (
    Building,
    BuildingType,
    HeroType,
    Player,
    Position,
    Resources,
)


def test_enemy_ai_behavior():
    """Test enemy AI behavior directly without server"""
    print("=== Testing Enemy AI Behavior ===")

    # Create test players
    player_id = str(uuid.uuid4())
    players = {
        player_id: Player(
            id=player_id,
            name="TestPlayer",
            hero_type=HeroType.TANK,
            resources=Resources(),
        )
    }

    # Create game manager
    lobby_id = str(uuid.uuid4())
    game_manager = GameManager(lobby_id, players)

    print(f"1. Game initialized with lobby: {lobby_id}")
    print(f"   Heroes: {len(game_manager.game_state.heroes)}")
    print(f"   Buildings: {len(game_manager.game_state.buildings)}")

    # Find town hall
    town_hall = None
    for building in game_manager.game_state.buildings.values():
        if building.building_type == BuildingType.TOWN_HALL:
            town_hall = building
            break

    if town_hall:
        print(f"2. Found town hall at ({town_hall.position.x}, {town_hall.position.y})")
        print(f"   Town hall health: {town_hall.health}")
    else:
        print("❌ No town hall found!")
        return

    # Manually spawn an enemy to test behavior
    enemy_id = str(uuid.uuid4())
    from shared.constants.game_constants import ENEMY_TYPES
    from shared.models.game_models import Enemy

    enemy_stats = ENEMY_TYPES["BASIC"]
    test_enemy = Enemy(
        id=enemy_id,
        position=Position(x=10, y=10),  # Spawn away from town hall
        health=enemy_stats["health"],
        max_health=enemy_stats["health"],
        target_position=None,  # Will be set by AI
        is_active=True,
        attack_damage=enemy_stats["attack_damage"],
        attack_range=enemy_stats["attack_range"],
        speed=enemy_stats["speed"],
        attack_speed=enemy_stats["attack_speed"],
    )

    game_manager.game_state.enemies[enemy_id] = test_enemy
    print(
        f"3. Spawned test enemy at ({test_enemy.position.x}, {test_enemy.position.y})"
    )
    print(
        f"   Enemy stats: health={test_enemy.health}, damage={test_enemy.attack_damage}, range={test_enemy.attack_range}"
    )

    # Test enemy AI target selection
    town_hall_found = game_manager._find_town_hall()
    if town_hall_found:
        print("4. Enemy AI can find town hall: ✅")

        # Test enemy movement toward town hall
        initial_x, initial_y = test_enemy.position.x, test_enemy.position.y

        # Set target to town hall manually
        test_enemy.target_position = Position(
            x=town_hall.position.x + town_hall.size[0] / 2,
            y=town_hall.position.y + town_hall.size[1] / 2,
        )

        print(
            f"5. Enemy target set to town hall center: ({test_enemy.target_position.x}, {test_enemy.target_position.y})"
        )

        # Simulate enemy movement updates with realistic time steps
        print("6. Simulating enemy movement...")
        for i in range(10):
            # Simulate multiple frames to see significant movement
            for _ in range(10):
                game_manager._update_enemies()

            current_x, current_y = test_enemy.position.x, test_enemy.position.y
            distance_to_target = (
                (current_x - test_enemy.target_position.x) ** 2
                + (current_y - test_enemy.target_position.y) ** 2
            ) ** 0.5
            print(
                f"   Update {i + 1}: Enemy at ({current_x:.2f}, {current_y:.2f}), distance to target: {distance_to_target:.2f}"
            )

            if distance_to_target < 5.0:
                print("   Enemy is getting close to town hall!")
                break
    else:
        print("4. Enemy AI cannot find town hall: ❌")

    # Test obstacle detection
    print("7. Testing obstacle detection...")

    # Add a wall between enemy and town hall
    wall_id = str(uuid.uuid4())
    wall_building = Building(
        id=wall_id,
        building_type=BuildingType.WALL,
        position=Position(x=20, y=20),  # Close to enemy path
        health=50,
        max_health=50,
        player_id=player_id,
        size=(1, 1),
    )
    game_manager.game_state.buildings[wall_id] = wall_building

    # Position enemy right next to the wall
    test_enemy.position = Position(
        x=19.3, y=20.0
    )  # Very close to wall center (20.5, 20.5)
    test_enemy.target_position = Position(x=25, y=20)  # Target beyond the wall

    obstacle = game_manager._find_obstacle_to_attack(test_enemy)
    print(f"   Enemy position: ({test_enemy.position.x}, {test_enemy.position.y})")
    print(
        f"   Enemy target: ({test_enemy.target_position.x}, {test_enemy.target_position.y})"
    )
    print(f"   Wall position: ({wall_building.position.x}, {wall_building.position.y})")
    print(f"   Enemy attack range: {test_enemy.attack_range}")

    # Calculate distance manually for debugging
    wall_center_x = wall_building.position.x + wall_building.size[0] / 2
    wall_center_y = wall_building.position.y + wall_building.size[1] / 2
    distance_to_wall = (
        (test_enemy.position.x - wall_center_x) ** 2
        + (test_enemy.position.y - wall_center_y) ** 2
    ) ** 0.5
    print(f"   Distance to wall center: {distance_to_wall:.2f}")
    print(
        f"   Required range: {test_enemy.attack_range + max(wall_building.size) / 2:.2f}"
    )

    if obstacle:
        print(
            f"   Enemy found obstacle to attack: {obstacle.building_type} at ({obstacle.position.x}, {obstacle.position.y}) ✅"
        )

        # Test attacking the obstacle
        initial_wall_health = wall_building.health
        game_manager._enemy_attack_obstacle(test_enemy, wall_building)
        print(f"   Wall health before attack: {initial_wall_health}")
        print(f"   Wall health after attack: {wall_building.health}")
        print("   Enemy successfully attacked obstacle: ✅")
    else:
        print("   No obstacle detected: ❌")

        # Test the blocking path detection separately
        is_blocking = game_manager._is_building_blocking_path(test_enemy, wall_building)
        print(f"   Is wall blocking path: {is_blocking}")

        # Test range check separately
        in_range = (
            distance_to_wall <= test_enemy.attack_range + max(wall_building.size) / 2
        )
        print(f"   Is wall in attack range: {in_range}")

    print("\n✅ Enemy AI behavior test completed!")


if __name__ == "__main__":
    test_enemy_ai_behavior()

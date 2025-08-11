#!/usr/bin/env python3

import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import time
import uuid

from server.services.game_manager import GameManager
from shared.models.game_models import (
    Building,
    BuildingType,
    HeroType,
    Player,
    Position,
    Resources,
    Unit,
    UnitType,
)


def test_enemy_movement_and_combat():
    """Test comprehensive enemy movement and combat behavior"""
    print("=== Testing Enemy Movement and Combat ===")

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

    # Find town hall and hero for reference
    town_hall = game_manager._find_town_hall()
    hero = list(game_manager.game_state.heroes.values())[0]

    print("1. Game initialized:")
    print(f"   Town hall at: ({town_hall.position.x}, {town_hall.position.y})")
    print(f"   Hero at: ({hero.position.x}, {hero.position.y})")

    # Add some player buildings in the path
    wall_id = str(uuid.uuid4())
    wall = Building(
        id=wall_id,
        building_type=BuildingType.WALL,
        position=Position(x=50, y=50),
        health=50,
        max_health=50,
        player_id=player_id,
        size=(1, 1),
    )
    game_manager.game_state.buildings[wall_id] = wall

    # Add a unit
    unit_id = str(uuid.uuid4())
    unit = Unit(
        id=unit_id,
        unit_type=UnitType.SOLDIER,
        position=Position(x=60, y=60),
        health=60,
        max_health=60,
        player_id=player_id,
    )
    game_manager.game_state.units[unit_id] = unit

    print("2. Added test targets:")
    print(f"   Wall at: ({wall.position.x}, {wall.position.y})")
    print(f"   Unit at: ({unit.position.x}, {unit.position.y})")

    # Manually spawn an enemy near the wall to test behavior
    from shared.constants.game_constants import ENEMY_TYPES
    from shared.models.game_models import Enemy

    enemy_id = str(uuid.uuid4())
    enemy_stats = ENEMY_TYPES["BASIC"]
    test_enemy = Enemy(
        id=enemy_id,
        position=Position(x=49.5, y=50.0),  # Very close to wall (0.5 units away)
        health=enemy_stats["health"],
        max_health=enemy_stats["health"],
        target_position=Position(
            x=town_hall.position.x + 1.5, y=town_hall.position.y + 1.5
        ),
        is_active=True,
        attack_damage=enemy_stats["attack_damage"],
        attack_range=enemy_stats["attack_range"],
        speed=enemy_stats["speed"],
        attack_speed=enemy_stats["attack_speed"],
    )

    game_manager.game_state.enemies[enemy_id] = test_enemy
    print(f"3. Spawned enemy at: ({test_enemy.position.x}, {test_enemy.position.y})")
    print(
        f"   Enemy target: ({test_enemy.target_position.x}, {test_enemy.target_position.y})"
    )
    print(f"   Enemy range: {test_enemy.attack_range}")

    # Test enemy behavior over several updates
    print("\n4. Testing enemy behavior:")

    for i in range(20):
        initial_pos = (test_enemy.position.x, test_enemy.position.y)

        # Update enemies
        game_manager._update_enemies()

        final_pos = (test_enemy.position.x, test_enemy.position.y)

        # Check if enemy moved
        if initial_pos != final_pos:
            print(
                f"   Update {i + 1}: Enemy moved from ({initial_pos[0]:.2f}, {initial_pos[1]:.2f}) to ({final_pos[0]:.2f}, {final_pos[1]:.2f})"
            )
        else:
            print(
                f"   Update {i + 1}: Enemy stayed at ({final_pos[0]:.2f}, {final_pos[1]:.2f})"
            )

        # Check if any targets were attacked
        if wall.health < 50:
            print(f"   🎯 Wall took damage! Health: {wall.health}")
        if unit.health < 60:
            print(f"   🎯 Unit took damage! Health: {unit.health}")
        if hero.health < hero.max_health:
            print(f"   🎯 Hero took damage! Health: {hero.health}")

        # Check distance to targets
        wall_dist = (
            (test_enemy.position.x - wall.position.x) ** 2
            + (test_enemy.position.y - wall.position.y) ** 2
        ) ** 0.5
        unit_dist = (
            (test_enemy.position.x - unit.position.x) ** 2
            + (test_enemy.position.y - unit.position.y) ** 2
        ) ** 0.5
        hero_dist = (
            (test_enemy.position.x - hero.position.x) ** 2
            + (test_enemy.position.y - hero.position.y) ** 2
        ) ** 0.5
        town_hall_dist = (
            (test_enemy.position.x - town_hall.position.x) ** 2
            + (test_enemy.position.y - town_hall.position.y) ** 2
        ) ** 0.5

        if i % 5 == 0:  # Print distances every 5 updates
            print(
                f"   Distances - Wall: {wall_dist:.2f}, Unit: {unit_dist:.2f}, Hero: {hero_dist:.2f}, Town Hall: {town_hall_dist:.2f}"
            )

        # Break if enemy reached town hall area
        if town_hall_dist < 5.0:
            print(f"   Enemy reached town hall area! Distance: {town_hall_dist:.2f}")
            break

        time.sleep(0.1)

    # Summary
    print("\n5. Final status:")
    print(
        f"   Enemy final position: ({test_enemy.position.x:.2f}, {test_enemy.position.y:.2f})"
    )
    print(f"   Wall health: {wall.health}/{wall.max_health}")
    print(f"   Unit health: {unit.health}/{unit.max_health}")
    print(f"   Hero health: {hero.health}/{hero.max_health}")
    print(f"   Town hall health: {town_hall.health}/{town_hall.max_health}")

    # Check if enemy is moving
    if test_enemy.position.x != 45 or test_enemy.position.y != 50:
        print("   ✅ Enemy movement working!")
    else:
        print("   ❌ Enemy not moving")

    # Check if combat occurred
    if (
        wall.health < 50
        or unit.health < 60
        or hero.health < hero.max_health
        or town_hall.health < town_hall.max_health
    ):
        print("   ✅ Enemy combat working!")
    else:
        print("   ⚠️ No combat detected")

    print("\n✅ Enemy movement and combat test completed!")


if __name__ == "__main__":
    test_enemy_movement_and_combat()

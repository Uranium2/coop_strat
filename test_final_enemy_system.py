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
)


def test_final_enemy_system():
    """Final test of complete enemy system"""
    print("=== Final Enemy System Test ===")

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

    # Get initial state
    town_hall = game_manager._find_town_hall()
    hero = list(game_manager.game_state.heroes.values())[0]

    print("1. Initial State:")
    print(
        f"   Town hall: ({town_hall.position.x}, {town_hall.position.y}) - Health: {town_hall.health}"
    )
    print(f"   Hero: ({hero.position.x}, {hero.position.y}) - Health: {hero.health}")
    print(f"   Time to first wave: {game_manager.game_state.time_to_next_wave:.1f}s")

    # Add a defensive wall near town hall
    wall_id = str(uuid.uuid4())
    wall = Building(
        id=wall_id,
        building_type=BuildingType.WALL,
        position=Position(x=town_hall.position.x - 10, y=town_hall.position.y),
        health=50,
        max_health=50,
        player_id=player_id,
        size=(1, 1),
    )
    game_manager.game_state.buildings[wall_id] = wall
    print(f"   Added defensive wall: ({wall.position.x}, {wall.position.y})")

    # Manually add an enemy to test movement (simulating wave spawn)
    from shared.constants.game_constants import ENEMY_TYPES
    from shared.models.game_models import Enemy

    enemy_id = str(uuid.uuid4())
    enemy_stats = ENEMY_TYPES["BASIC"]

    # Find actual town hall and spawn enemy at corner moving toward it
    town_hall_target = Position(
        x=town_hall.position.x + town_hall.size[0] / 2,
        y=town_hall.position.y + town_hall.size[1] / 2,
    )

    test_enemy = Enemy(
        id=enemy_id,
        position=Position(x=10, y=10),  # Start from corner like real spawn
        health=enemy_stats["health"],
        max_health=enemy_stats["health"],
        target_position=town_hall_target,
        is_active=True,
        attack_damage=enemy_stats["attack_damage"],
        attack_range=enemy_stats["attack_range"],
        speed=enemy_stats["speed"],
        attack_speed=enemy_stats["attack_speed"],
    )

    game_manager.game_state.enemies[enemy_id] = test_enemy
    print(
        f"2. Spawned test enemy at: ({test_enemy.position.x}, {test_enemy.position.y})"
    )
    print(
        f"   Target: ({test_enemy.target_position.x}, {test_enemy.target_position.y})"
    )

    # Test movement over time
    print("\n3. Testing enemy movement and combat:")

    for i in range(100):  # Increased from 30 to 100 updates
        game_manager.update()

        # Calculate distances
        enemy_pos = test_enemy.position
        wall_dist = (
            (enemy_pos.x - wall.position.x) ** 2 + (enemy_pos.y - wall.position.y) ** 2
        ) ** 0.5
        town_hall_dist = (
            (enemy_pos.x - town_hall_target.x) ** 2
            + (enemy_pos.y - town_hall_target.y) ** 2
        ) ** 0.5
        hero_dist = (
            (enemy_pos.x - hero.position.x) ** 2 + (enemy_pos.y - hero.position.y) ** 2
        ) ** 0.5

        if i % 20 == 0:  # Print every 20 updates
            print(
                f"   Update {i:2d}: Enemy at ({enemy_pos.x:5.1f}, {enemy_pos.y:5.1f})"
            )
            print(
                f"             Distances - Wall: {wall_dist:5.1f}, Town Hall: {town_hall_dist:5.1f}, Hero: {hero_dist:5.1f}"
            )
            print(
                f"             Health - Wall: {wall.health:3.0f}, Town Hall: {town_hall.health:4.0f}, Hero: {hero.health:3.0f}"
            )

        # Check if structures are under attack
        if wall.health < 50:
            print(f"   🎯 Wall under attack! Health: {wall.health}")
        if town_hall.health < 1000:
            print(f"   🚨 TOWN HALL UNDER ATTACK! Health: {town_hall.health}")
        if hero.health < 200:
            print(f"   🚨 HERO UNDER ATTACK! Health: {hero.health}")

        # Break if enemy gets close to town hall
        if town_hall_dist < 3.0:
            print(
                f"   ⚠️ Enemy reached town hall vicinity! Distance: {town_hall_dist:.1f}"
            )
            break

        time.sleep(0.02)  # Reduced delay

    print("\n4. Final Status:")
    print(
        f"   Enemy final position: ({test_enemy.position.x:.1f}, {test_enemy.position.y:.1f})"
    )
    print(f"   Wall health: {wall.health}/{wall.max_health}")
    print(f"   Town hall health: {town_hall.health}/{town_hall.max_health}")
    print(f"   Hero health: {hero.health}/{hero.max_health}")

    # Verify functionality
    movement_distance = (
        (test_enemy.position.x - 10) ** 2 + (test_enemy.position.y - 10) ** 2
    ) ** 0.5

    if movement_distance > 1.0:
        print(f"   ✅ Enemy movement: Working (moved {movement_distance:.1f} units)")
    else:
        print(
            f"   ❌ Enemy movement: Not working (moved {movement_distance:.1f} units)"
        )

    if wall.health < 50 or town_hall.health < 1000 or hero.health < 200:
        print("   ✅ Enemy combat: Working")
    else:
        print("   ⚠️ Enemy combat: No combat detected")

    print("\n✅ Final enemy system test completed!")


if __name__ == "__main__":
    test_final_enemy_system()

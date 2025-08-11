#!/usr/bin/env python3
"""Debug attack range calculation"""

import asyncio
import logging
from typing import Dict

from server.services.game_manager import GameManager
from shared.models.game_models import (
    BuildingType,
    Player,
    Resources,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def debug_attack_range():
    """Debug why enemies aren't attacking the town hall"""
    print("=== Debugging Attack Range ===")

    # Create a test player
    test_player = Player(
        id="player1",
        name="TestPlayer",
        hero_type="TANK",
        resources=Resources(wood=100, stone=100, food=100),
    )
    players: Dict[str, Player] = {"player1": test_player}

    # Create game manager
    game_manager = GameManager("test_lobby", players)

    # Get the town hall
    town_hall = None
    for building in game_manager.game_state.buildings.values():
        if building.building_type == BuildingType.TOWN_HALL:
            town_hall = building
            break

    print("Town hall:")
    print(f"  Position: ({town_hall.position.x}, {town_hall.position.y})")
    print(f"  Size: {town_hall.size}")
    print(
        f"  Center: ({town_hall.position.x + town_hall.size[0] / 2}, {town_hall.position.y + town_hall.size[1] / 2})"
    )
    print(f"  Player ID: {town_hall.player_id}")

    # Spawn enemies
    game_manager._spawn_enemy_wave()
    enemy = next(iter(game_manager.game_state.enemies.values()))

    print("\nEnemy:")
    print(f"  Position: ({enemy.position.x}, {enemy.position.y})")
    print(f"  Attack range: {enemy.attack_range}")
    print(f"  Attack damage: {enemy.attack_damage}")

    # Place enemy very close to town hall to test attack
    town_hall_center_x = town_hall.position.x + town_hall.size[0] / 2
    town_hall_center_y = town_hall.position.y + town_hall.size[1] / 2

    # Place enemy at different distances to test attack range
    test_distances = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0]

    for test_distance in test_distances:
        # Reset town hall health for each test
        town_hall.health = 1000

        # Place enemy at test distance from town hall center
        enemy.position.x = town_hall_center_x - test_distance
        enemy.position.y = town_hall_center_y

        print(f"\n--- Testing distance {test_distance} ---")
        print(f"Enemy position: ({enemy.position.x:.2f}, {enemy.position.y:.2f})")

        # Calculate distance manually
        dx = town_hall_center_x - enemy.position.x
        dy = town_hall_center_y - enemy.position.y
        actual_distance = (dx * dx + dy * dy) ** 0.5
        print(f"Actual distance to town hall center: {actual_distance:.2f}")

        # Calculate effective range
        effective_range = enemy.attack_range + max(town_hall.size) / 2
        print(
            f"Effective attack range: {enemy.attack_range} + {max(town_hall.size) / 2} = {effective_range}"
        )
        print(f"Can attack: {actual_distance <= effective_range}")

        # Test if enemy finds target to attack
        target_info = game_manager._find_target_to_attack(enemy)
        if target_info:
            target_type, target, distance = target_info
            print(f"Target found: {target_type}, distance: {distance:.2f}")

            # Perform attack
            initial_health = town_hall.health
            game_manager._enemy_attack_target(enemy, target_info)
            print(f"Town hall health: {initial_health} -> {town_hall.health}")
        else:
            print("No target found - enemy will not attack")


if __name__ == "__main__":
    asyncio.run(debug_attack_range())

#!/usr/bin/env python3
"""Test script to verify enemies attack and damage the town hall"""

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


async def test_enemy_town_hall_attack():
    """Test that enemies attack and damage the town hall"""
    print("=== Testing Enemy Town Hall Attack ===")

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

    print("Game initialized")
    print(f"Game is_active: {game_manager.game_state.is_active}")

    # Get the town hall
    town_hall = None
    for building in game_manager.game_state.buildings.values():
        if building.building_type == BuildingType.TOWN_HALL:
            town_hall = building
            break

    if not town_hall:
        print("ERROR: No town hall found!")
        return

    print(
        f"Town hall found: ID={town_hall.id}, Health={town_hall.health}, Position=({town_hall.position.x}, {town_hall.position.y})"
    )

    # Force spawn enemies
    print("\n--- Force spawning enemies ---")
    game_manager._spawn_enemy_wave()
    print(f"Enemies spawned: {len(game_manager.game_state.enemies)}")

    if not game_manager.game_state.enemies:
        print("ERROR: No enemies spawned!")
        return

    # Show enemy info
    for enemy_id, enemy in game_manager.game_state.enemies.items():
        print(
            f"Enemy {enemy_id}: Position=({enemy.position.x}, {enemy.position.y}), Target=({enemy.target_position.x if enemy.target_position else 'None'}, {enemy.target_position.y if enemy.target_position else 'None'})"
        )

    print("\n--- Simulating game updates until town hall is attacked ---")
    initial_health = town_hall.health
    update_count = 0
    max_updates = 100  # Prevent infinite loop

    while town_hall.health == initial_health and update_count < max_updates:
        # Update the game (this should move enemies and process combat)
        game_manager.update()
        update_count += 1

        if update_count % 10 == 0:
            print(f"Update {update_count}: Town hall health = {town_hall.health}")
            # Show closest enemy to town hall
            closest_distance = float("inf")
            closest_enemy = None
            for enemy in game_manager.game_state.enemies.values():
                distance = (
                    (enemy.position.x - town_hall.position.x) ** 2
                    + (enemy.position.y - town_hall.position.y) ** 2
                ) ** 0.5
                if distance < closest_distance:
                    closest_distance = distance
                    closest_enemy = enemy

            if closest_enemy:
                print(
                    f"  Closest enemy: Distance={closest_distance:.1f}, Position=({closest_enemy.position.x:.1f}, {closest_enemy.position.y:.1f})"
                )

    print(f"\nFinal results after {update_count} updates:")
    print(f"Town hall health: {initial_health} -> {town_hall.health}")
    print(f"Damage taken: {initial_health - town_hall.health}")
    print(f"Game is_active: {game_manager.game_state.is_active}")
    print(f"Game over reason: {game_manager.game_state.game_over_reason}")

    if town_hall.health < initial_health:
        print("✅ SUCCESS: Town hall took damage from enemies")
    else:
        print("❌ FAILED: Town hall did not take any damage")

    if town_hall.health <= 0:
        print("✅ Town hall was destroyed")
        if not game_manager.game_state.is_active:
            print("✅ Game correctly ended")
        else:
            print("❌ Game should have ended but didn't")
    else:
        print(f"ℹ️  Town hall survived with {town_hall.health} health")


if __name__ == "__main__":
    asyncio.run(test_enemy_town_hall_attack())

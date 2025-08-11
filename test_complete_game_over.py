#!/usr/bin/env python3
"""Test that enemies eventually reach and destroy the town hall"""

import asyncio
import logging
import time
from typing import Dict

from server.services.game_manager import GameManager
from shared.models.game_models import (
    BuildingType,
    GameOverReason,
    Player,
    Resources,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_complete_game_over_flow():
    """Test the complete flow from enemy spawn to town hall destruction"""
    print("=== Testing Complete Game Over Flow ===")

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

    print(
        f"Town hall: Health={town_hall.health}, Position=({town_hall.position.x}, {town_hall.position.y})"
    )

    # Spawn enemies
    game_manager._spawn_enemy_wave()
    print(f"Enemies spawned: {len(game_manager.game_state.enemies)}")

    # Speed up the process by setting enemies closer and with higher speed
    for enemy in game_manager.game_state.enemies.values():
        # Place enemy closer to town hall for faster testing
        enemy.position.x = 80.0  # Closer to town hall at (100, 100)
        enemy.position.y = 80.0
        enemy.speed = 10.0  # Much faster movement
        enemy.attack_damage = 200  # Much higher damage to destroy town hall faster
        print(
            f"Enemy {enemy.id}: Position=({enemy.position.x}, {enemy.position.y}), Speed={enemy.speed}, Damage={enemy.attack_damage}"
        )

    print("\n--- Running game updates until town hall is destroyed ---")
    initial_health = town_hall.health
    update_count = 0
    max_updates = 1000  # Allow more updates

    while (
        town_hall.health > 0
        and update_count < max_updates
        and game_manager.game_state.is_active
    ):
        # Wait for proper timing
        time.sleep(1.0 / game_manager.tick_rate + 0.001)

        # Update the game
        game_manager.update()
        update_count += 1

        if update_count % 60 == 0:  # Print every second (60 FPS)
            print(
                f"Update {update_count}: Town hall health = {town_hall.health}/{initial_health}"
            )
            # Show closest enemy to town hall
            closest_distance = float("inf")
            for enemy in game_manager.game_state.enemies.values():
                distance = (
                    (enemy.position.x - town_hall.position.x) ** 2
                    + (enemy.position.y - town_hall.position.y) ** 2
                ) ** 0.5
                if distance < closest_distance:
                    closest_distance = distance
            print(f"  Closest enemy distance: {closest_distance:.1f}")

    print("\n=== FINAL RESULTS ===")
    print(f"Updates performed: {update_count}")
    print(f"Town hall health: {initial_health} -> {town_hall.health}")
    print(f"Game is_active: {game_manager.game_state.is_active}")
    print(f"Game over reason: {game_manager.game_state.game_over_reason}")

    if town_hall.health <= 0:
        print("✅ Town hall was destroyed!")
        if not game_manager.game_state.is_active:
            print("✅ Game correctly ended (is_active=False)")
        else:
            print("❌ Game should have ended but is_active is still True")

        if (
            game_manager.game_state.game_over_reason
            == GameOverReason.TOWN_HALL_DESTROYED
        ):
            print("✅ Game over reason correctly set")
        else:
            print(
                f"❌ Wrong game over reason: {game_manager.game_state.game_over_reason}"
            )
    else:
        print("❌ Town hall was not destroyed within time limit")


if __name__ == "__main__":
    asyncio.run(test_complete_game_over_flow())

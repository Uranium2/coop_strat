#!/usr/bin/env python3
"""Debug enemy movement and AI issues"""

import asyncio
import logging
import time
from typing import Dict

from server.services.game_manager import GameManager
from shared.models.game_models import (
    Player,
    Resources,
)

# Configure logging for detailed debug output
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


async def debug_enemy_ai():
    """Debug why enemies aren't moving"""
    print("=== Debugging Enemy AI ===")

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
    print(f"Game is_paused: {game_manager.game_state.is_paused}")

    # Force spawn enemies
    print("\n--- Force spawning enemies ---")
    game_manager._spawn_enemy_wave()
    print(f"Enemies spawned: {len(game_manager.game_state.enemies)}")

    if not game_manager.game_state.enemies:
        print("ERROR: No enemies spawned!")
        return

    # Get one enemy to debug
    enemy_id, enemy = next(iter(game_manager.game_state.enemies.items()))
    print(f"\nDebugging enemy {enemy_id}:")
    print(f"  Initial position: ({enemy.position.x}, {enemy.position.y})")
    print(
        f"  Target position: ({enemy.target_position.x if enemy.target_position else 'None'}, {enemy.target_position.y if enemy.target_position else 'None'})"
    )
    print(f"  Health: {enemy.health}")
    print(f"  Speed: {enemy.speed}")

    # Perform a few updates with detailed logging
    print("\n--- Performing updates ---")
    for i in range(3):
        print(f"\n  Update {i + 1}:")
        print(f"    Before: Position=({enemy.position.x:.2f}, {enemy.position.y:.2f})")
        print(
            f"    Target: ({enemy.target_position.x:.2f}, {enemy.target_position.y:.2f})"
        )
        print(f"    Speed: {enemy.speed}")
        print(f"    Tick rate: {game_manager.tick_rate}")
        print(f"    dt (1/tick_rate): {1.0 / game_manager.tick_rate}")

        # Calculate expected movement manually
        dx = enemy.target_position.x - enemy.position.x
        dy = enemy.target_position.y - enemy.position.y
        distance = (dx * dx + dy * dy) ** 0.5
        dt = 1.0 / game_manager.tick_rate
        move_distance = enemy.speed * dt
        print(f"    Distance to target: {distance:.2f}")
        print(f"    Expected move distance: {move_distance:.4f}")

        # Wait for sufficient time to trigger update
        time.sleep(
            dt + 0.001
        )  # Sleep slightly longer than dt to ensure update triggers

        # Call update
        game_manager.update()

        # Check if enemy moved
        new_position = game_manager.game_state.enemies[enemy_id].position
        print(f"    After:  Position=({new_position.x:.2f}, {new_position.y:.2f})")

        distance_moved = (
            (new_position.x - enemy.position.x) ** 2
            + (new_position.y - enemy.position.y) ** 2
        ) ** 0.5
        print(f"    Distance moved: {distance_moved:.4f}")

        enemy = game_manager.game_state.enemies[enemy_id]  # Update reference


if __name__ == "__main__":
    asyncio.run(debug_enemy_ai())

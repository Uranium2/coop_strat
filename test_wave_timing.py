#!/usr/bin/env python3
"""
Test actual wave timing system
"""

import asyncio
import time
from typing import Dict

from server.services.game_manager import GameManager
from shared.models.game_models import Player, Resources


async def test_wave_timing():
    print("=== Testing Wave Timing System ===")

    # Create a test lobby with one player
    lobby_id = "test-lobby"
    test_player = Player(
        id="player1",
        name="TestPlayer",
        hero_type="TANK",
        resources=Resources(wood=100, stone=100, food=100),
    )
    players: Dict[str, Player] = {"player1": test_player}

    # Create game manager
    game_manager = GameManager(lobby_id, players)

    print(f"Initial next_wave_time: {game_manager.game_state.next_wave_time}")
    print(f"Current time: {time.time()}")
    print(
        f"Time until first wave: {game_manager.game_state.next_wave_time - time.time():.1f} seconds"
    )

    # Check if the game updates properly detect wave spawning
    current_time = time.time()
    print(f"\nFirst wave should spawn at: {game_manager.game_state.next_wave_time}")
    print(f"Current time: {current_time}")
    print(f"Should spawn now? {current_time >= game_manager.game_state.next_wave_time}")

    # Run a few updates to see the timing system
    print("\n--- Running updates ---")
    for i in range(10):
        game_state = game_manager.update()
        current_time = time.time()

        print(f"Update {i + 1}:")
        print(f"  Current time: {current_time}")
        print(f"  Next wave time: {game_manager.game_state.next_wave_time}")
        print(
            f"  Should spawn: {current_time >= game_manager.game_state.next_wave_time}"
        )
        print(f"  Enemy count: {len(game_manager.game_state.enemies)}")
        print(f"  State changed: {game_state is not None}")

        if len(game_manager.game_state.enemies) > 0:
            print("  ENEMIES SPAWNED!")
            break

        await asyncio.sleep(0.1)

    print("=== Test Complete ===")


if __name__ == "__main__":
    asyncio.run(test_wave_timing())

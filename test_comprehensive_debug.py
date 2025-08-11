#!/usr/bin/env python3
"""
Comprehensive test to identify exactly why enemies aren't moving in the real game
"""

import asyncio
import logging
import time
from typing import Dict

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

from server.services.game_manager import GameManager
from shared.models.game_models import Player, Resources


async def test_real_game_scenario():
    print("=== Comprehensive Enemy Movement Test ===")

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

    print("Game initialized")
    print(f"Game is_paused: {game_manager.game_state.is_paused}")
    print(f"Game is_active: {game_manager.game_state.is_active}")
    print(f"Tick rate: {game_manager.tick_rate}")

    # Force spawn enemies
    print("\n--- Force spawning enemies ---")
    game_manager._spawn_enemy_wave()
    print(f"Enemies spawned: {len(game_manager.game_state.enemies)}")

    if not game_manager.game_state.enemies:
        print("ERROR: No enemies spawned!")
        return

    # Show initial enemy state
    print("\n--- Initial Enemy State ---")
    for enemy_id, enemy in game_manager.game_state.enemies.items():
        print(f"Enemy {enemy_id[:8]}:")
        print(f"  Position: ({enemy.position.x}, {enemy.position.y})")
        print(
            f"  Target: {(enemy.target_position.x, enemy.target_position.y) if enemy.target_position else 'None'}"
        )
        print(f"  Speed: {enemy.speed}")
        print(f"  Active: {enemy.is_active}")
        print(f"  Health: {enemy.health}")
        print(f"  Dead: {enemy.is_dead}")

    # Simulate exact game loop behavior
    print("\n--- Simulating Game Loop (exactly like server/main.py) ---")
    loop_count = 0
    max_loops = 300  # 5 seconds worth

    while loop_count < max_loops:
        # Sleep exactly like the real game loop
        await asyncio.sleep(1 / 60)

        # Call update exactly like the real game loop
        start_time = time.time()
        game_state = game_manager.update()
        end_time = time.time()

        # Check every second (60 loops)
        if loop_count % 60 == 0:
            print(f"\n--- After {loop_count // 60} seconds ---")
            print(f"Update time: {end_time - start_time:.6f}s")
            print(f"State changed: {game_state is not None}")
            print(f"Current game time: {game_manager.game_state.game_time:.2f}")
            print(f"Last update: {game_manager.last_update}")

            # Check enemy positions
            moved_count = 0
            for enemy_id, enemy in game_manager.game_state.enemies.items():
                # Compare with initial positions (approximately)
                initial_positions = [
                    (0.0, 0.0),
                    (199.0, 0.0),
                    (0.0, 199.0),
                    (199.0, 199.0),
                ]
                moved = False
                for init_pos in initial_positions:
                    if (
                        abs(enemy.position.x - init_pos[0]) > 1.0
                        or abs(enemy.position.y - init_pos[1]) > 1.0
                    ):
                        moved = True
                        break
                if moved:
                    moved_count += 1

                print(
                    f"  Enemy {enemy_id[:8]}: ({enemy.position.x:.2f}, {enemy.position.y:.2f})"
                )

            print(
                f"Enemies that moved from spawn: {moved_count}/{len(game_manager.game_state.enemies)}"
            )

            if moved_count > 0:
                print("SUCCESS: Enemies are moving!")
                break

        loop_count += 1

    if loop_count >= max_loops:
        print("\nERROR: No enemy movement detected after 5 seconds!")

        # Final debug info
        print("\n--- Final Debug Info ---")
        print(f"Game paused: {game_manager.game_state.is_paused}")
        print(f"Game active: {game_manager.game_state.is_active}")
        print(f"State changed flag: {game_manager.state_changed}")
        print(f"Current time: {time.time()}")
        print(f"Last update: {game_manager.last_update}")
        print(f"Tick rate: {game_manager.tick_rate}")

        # Check if updates are being called
        old_update = game_manager.last_update
        game_manager.update()
        new_update = game_manager.last_update
        print(f"Update called manually - time changed: {old_update != new_update}")

    print("=== Test Complete ===")


if __name__ == "__main__":
    asyncio.run(test_real_game_scenario())

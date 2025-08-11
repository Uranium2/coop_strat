#!/usr/bin/env python3
"""
Test to verify enemy spawning works immediately in a real game scenario.
"""

import asyncio
from typing import Dict

from server.services.game_manager import GameManager
from shared.models.game_models import Player, Resources


async def test_immediate_enemy_spawn():
    print("=== Testing Immediate Enemy Spawn ===")

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

    print(
        f"Game initialized with town hall at: {[b.position for b in game_manager.game_state.buildings.values() if b.building_type.value == 'TOWN_HALL']}"
    )
    print(f"Initial enemy count: {len(game_manager.game_state.enemies)}")

    # Force immediate enemy spawn by calling the spawn method directly
    print("\n--- Forcing immediate enemy wave spawn ---")
    game_manager._spawn_enemy_wave()

    print(f"Enemy count after spawn: {len(game_manager.game_state.enemies)}")

    if game_manager.game_state.enemies:
        print("\nSpawned enemies:")
        for enemy_id, enemy in game_manager.game_state.enemies.items():
            print(f"  Enemy {enemy_id[:8]}...")
            print(f"    Position: ({enemy.position.x}, {enemy.position.y})")
            print(
                f"    Target: ({enemy.target_position.x}, {enemy.target_position.y}) if enemy.target_position else None"
            )
            print(f"    Speed: {enemy.speed}")
            print(f"    Active: {enemy.is_active}")
            print(f"    Health: {enemy.health}")

    # Test a few game updates to see if they move
    print("\n--- Testing movement over 5 updates ---")
    for i in range(5):
        game_state = game_manager.update()
        print(f"Update {i + 1}: State changed = {game_state is not None}")

        if i == 4:  # After final update
            print("\nFinal enemy positions:")
            for enemy_id, enemy in game_manager.game_state.enemies.items():
                print(
                    f"  Enemy {enemy_id[:8]}: ({enemy.position.x:.2f}, {enemy.position.y:.2f})"
                )

        await asyncio.sleep(1 / 60)  # 60 FPS

    print("=== Test Complete ===")


if __name__ == "__main__":
    asyncio.run(test_immediate_enemy_spawn())

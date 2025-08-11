#!/usr/bin/env python3
"""
Test enemy movement with comprehensive debug logging to identify the issue.
"""

import asyncio
import uuid
from typing import Dict

from server.services.game_manager import GameManager
from shared.models.game_models import Player


async def test_enemy_movement_with_debug():
    print("=== Enemy Movement Debug Test ===")

    # Create a test lobby with one player
    lobby_id = "test-lobby"
    from shared.models.game_models import Resources

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
        f"Game initialized with town hall at: {[b for b in game_manager.game_state.buildings.values() if b.building_type.value == 'TOWN_HALL']}"
    )

    # Force spawn one enemy for testing
    print("\n--- Manually spawning test enemy ---")
    enemy_id = str(uuid.uuid4())
    from shared.constants.game_constants import ENEMY_TYPES
    from shared.models.game_models import Enemy, Position

    enemy_stats = ENEMY_TYPES["BASIC"]
    test_enemy = Enemy(
        id=enemy_id,
        position=Position(x=5.0, y=5.0),  # Start at corner
        health=enemy_stats["health"],
        max_health=enemy_stats["health"],
        target_position=None,  # Will be set by update system
        is_active=True,
        attack_damage=enemy_stats["attack_damage"],
        attack_range=enemy_stats["attack_range"],
        speed=enemy_stats["speed"],
        attack_speed=enemy_stats["attack_speed"],
    )

    game_manager.game_state.enemies[enemy_id] = test_enemy
    print(
        f"Spawned enemy {enemy_id} at position ({test_enemy.position.x}, {test_enemy.position.y})"
    )
    print(f"Enemy speed: {test_enemy.speed}")
    print(f"Enemy is_active: {test_enemy.is_active}")
    print(f"Enemy health: {test_enemy.health}")

    # Run game updates for 3 seconds to observe movement
    print("\n--- Running game updates ---")
    update_count = 0
    max_updates = 180  # 3 seconds at 60 FPS

    while update_count < max_updates:
        # Call the update method
        game_state = game_manager.update()

        # Check enemy position every 30 updates (0.5 seconds)
        if update_count % 30 == 0:
            enemy = game_manager.game_state.enemies.get(enemy_id)
            if enemy:
                print(
                    f"Update {update_count}: Enemy at ({enemy.position.x:.2f}, {enemy.position.y:.2f})"
                )
                if enemy.target_position:
                    print(
                        f"  Target: ({enemy.target_position.x:.2f}, {enemy.target_position.y:.2f})"
                    )
                else:
                    print("  No target position set!")
            else:
                print(f"Update {update_count}: Enemy not found!")
                break

        update_count += 1
        await asyncio.sleep(1 / 60)  # 60 FPS

    # Final position check
    final_enemy = game_manager.game_state.enemies.get(enemy_id)
    if final_enemy:
        print(
            f"\nFinal position: ({final_enemy.position.x:.2f}, {final_enemy.position.y:.2f})"
        )
        if final_enemy.target_position:
            distance = (
                (final_enemy.target_position.x - final_enemy.position.x) ** 2
                + (final_enemy.target_position.y - final_enemy.position.y) ** 2
            ) ** 0.5
            print(f"Distance to target: {distance:.2f}")
        print(f"Enemy is_active: {final_enemy.is_active}")
        print(f"Enemy health: {final_enemy.health}")

    print("=== Test Complete ===")


if __name__ == "__main__":
    asyncio.run(test_enemy_movement_with_debug())

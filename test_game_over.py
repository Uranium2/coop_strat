#!/usr/bin/env python3
"""
Test game over functionality when town hall is destroyed
"""

import asyncio
from typing import Dict

from server.services.game_manager import GameManager
from shared.models.game_models import GameOverReason, Player, Resources


async def test_game_over():
    print("=== Testing Game Over Functionality ===")

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
    print(f"Game is_active: {game_manager.game_state.is_active}")
    print(f"Game over reason: {game_manager.game_state.game_over_reason}")

    # Find the town hall
    town_hall = None
    for building in game_manager.game_state.buildings.values():
        if building.building_type.value == "TOWN_HALL":
            town_hall = building
            break

    if not town_hall:
        print("ERROR: No town hall found!")
        return

    print(f"Town hall found with {town_hall.health} health")

    # Destroy the town hall
    print("\n--- Destroying town hall ---")
    town_hall.health = 0
    print(f"Town hall health set to: {town_hall.health}")

    # Run game update to trigger game over check
    print("\n--- Running game update ---")
    game_state = game_manager.update()

    print("After update:")
    print(f"  Game is_active: {game_manager.game_state.is_active}")
    print(f"  Game over reason: {game_manager.game_state.game_over_reason}")
    print(f"  State changed: {game_state is not None}")

    # Verify game over state
    if (
        not game_manager.game_state.is_active
        and game_manager.game_state.game_over_reason
        == GameOverReason.TOWN_HALL_DESTROYED
    ):
        print("✅ SUCCESS: Game over detected correctly!")
    else:
        print("❌ FAILED: Game over not working properly")

    print("=== Test Complete ===")


if __name__ == "__main__":
    asyncio.run(test_game_over())

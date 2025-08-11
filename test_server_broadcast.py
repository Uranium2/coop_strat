#!/usr/bin/env python3
"""Test that server properly broadcasts game over state"""

import asyncio
import logging
import time
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


async def test_server_game_over_broadcast():
    """Test that server broadcasts game over state correctly"""
    print("=== Testing Server Game Over Broadcast ===")

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

    print("Initial state:")
    print(f"  Town hall health: {town_hall.health}")
    print(f"  Game is_active: {game_manager.game_state.is_active}")
    print(f"  Game over reason: {game_manager.game_state.game_over_reason}")
    print(f"  State changed: {game_manager.state_changed}")

    # Destroy town hall
    print("\nDestroying town hall...")
    town_hall.health = 0
    game_manager._check_game_over()

    print("After _check_game_over():")
    print(f"  Game is_active: {game_manager.game_state.is_active}")
    print(f"  Game over reason: {game_manager.game_state.game_over_reason}")
    print(f"  State changed: {game_manager.state_changed}")

    # Test multiple update calls to see when state is returned
    print("\nTesting update() calls:")
    for i in range(5):
        time.sleep(0.1)  # Wait 100ms between updates
        returned_state = game_manager.update()

        if returned_state:
            print(f"  Update {i + 1}: State returned!")
            print(f"    is_active: {returned_state.is_active}")
            print(f"    game_over_reason: {returned_state.game_over_reason}")
            print(f"    state_changed after return: {game_manager.state_changed}")
            break
        else:
            print(
                f"  Update {i + 1}: No state returned (state_changed={game_manager.state_changed})"
            )

    # Direct state check
    print("\nDirect state check (get_game_state()):")
    current_state = game_manager.get_game_state()
    print(f"  is_active: {current_state.is_active}")
    print(f"  game_over_reason: {current_state.game_over_reason}")


if __name__ == "__main__":
    asyncio.run(test_server_game_over_broadcast())

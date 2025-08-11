#!/usr/bin/env python3
"""Test script to verify town hall destruction triggers game over"""

import asyncio
import logging
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


async def test_town_hall_destruction():
    """Test that destroying the town hall triggers game over"""
    print("=== Testing Town Hall Destruction ===")

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
    print(f"Game over reason: {game_manager.game_state.game_over_reason}")

    # Get the town hall
    town_hall = None
    for building in game_manager.game_state.buildings.values():
        if building.building_type == BuildingType.TOWN_HALL:
            town_hall = building
            break

    if not town_hall:
        print("ERROR: No town hall found!")
        return

    print(f"Town hall found: ID={town_hall.id}, Health={town_hall.health}")
    print(f"Game state - is_active: {game_manager.game_state.is_active}")
    print(f"Game state - game_over_reason: {game_manager.game_state.game_over_reason}")

    # Damage the town hall to simulate destruction
    print(f"\nDestroying town hall (current health: {town_hall.health})...")
    town_hall.health = 0

    # Manually call game over check (this should normally happen in update loop)
    game_manager._check_game_over()

    print("\nAfter destruction:")
    print(f"Town hall health: {town_hall.health}")
    print(f"Game state - is_active: {game_manager.game_state.is_active}")
    print(f"Game state - game_over_reason: {game_manager.game_state.game_over_reason}")

    # Verify game over state
    if not game_manager.game_state.is_active:
        print("✅ SUCCESS: Game correctly marked as inactive")
    else:
        print("❌ FAILED: Game should be inactive but is still active")

    if game_manager.game_state.game_over_reason == GameOverReason.TOWN_HALL_DESTROYED:
        print("✅ SUCCESS: Game over reason correctly set to TOWN_HALL_DESTROYED")
    else:
        print(
            f"❌ FAILED: Expected TOWN_HALL_DESTROYED, got {game_manager.game_state.game_over_reason}"
        )


if __name__ == "__main__":
    asyncio.run(test_town_hall_destruction())

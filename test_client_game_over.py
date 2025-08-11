#!/usr/bin/env python3

import asyncio
import logging

import pygame

from client.scenes.game_scene import GameScene
from client.utils.network_manager import NetworkManager
from shared.constants.game_constants import SCREEN_HEIGHT, SCREEN_WIDTH

# Set up logging
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def create_mock_game_state(is_active=True, game_over_reason="NONE"):
    """Create a mock game state for testing"""
    return {
        "is_active": is_active,
        "is_paused": False,
        "game_over_reason": game_over_reason,
        "lobby_id": "test-lobby",
        "wave_number": 1,
        "time_to_next_wave": 30,
        "map_data": [[0 for _ in range(50)] for _ in range(50)],
        "fog_of_war": [[True for _ in range(50)] for _ in range(50)],
        "heroes": {},
        "enemies": {},
        "buildings": {
            "town_hall": {
                "id": "town_hall",
                "building_type": "TOWN_HALL",
                "position": {"x": 25, "y": 25},
                "size": [2, 2],
                "health": 0 if not is_active else 1000,
                "max_health": 1000,
                "player_id": "player1",
            }
        },
        "units": {},
        "players": {
            "player1": {
                "id": "player1",
                "name": "TestPlayer",
                "resources": {
                    "wood": 100,
                    "stone": 100,
                    "wheat": 100,
                    "metal": 50,
                    "gold": 50,
                },
            }
        },
        "pings": {},
        "attack_effects": {},
    }


async def test_game_over_client():
    """Test game over detection on client side"""
    print("=== Testing Client Game Over Detection ===")

    # Initialize pygame
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

    # Create mock network manager
    network_manager = NetworkManager()
    network_manager.player_id = "player1"

    try:
        # Create game scene with active game state
        print("\n1. Creating GameScene with active game state...")
        active_game_state = create_mock_game_state(is_active=True)
        game_scene = GameScene(screen, network_manager, active_game_state)

        print("   GameScene created successfully")
        print(f"   Initial is_active: {game_scene.game_state.is_active}")
        print(f"   Initial game_over_reason: {game_scene.game_state.game_over_reason}")

        # Test that no next scene is set initially
        next_scene = game_scene.get_next_scene()
        print(f"   Initial next_scene: {next_scene}")

        # Simulate game over update
        print("\n2. Simulating game over update...")
        game_over_state = create_mock_game_state(
            is_active=False, game_over_reason="TOWN_HALL_DESTROYED"
        )

        # Call the game update handler directly
        game_scene._on_game_update({"game_state": game_over_state})

        print("   After game over update:")
        print(f"   is_active: {game_scene.game_state.is_active}")
        print(f"   game_over_reason: {game_scene.game_state.game_over_reason}")

        # Check if next scene was set
        next_scene = game_scene.get_next_scene()
        print(f"   next_scene: {type(next_scene).__name__ if next_scene else None}")

        if next_scene:
            print("✅ SUCCESS: Game over scene transition detected!")
            print(f"   Scene type: {type(next_scene).__name__}")
            if hasattr(next_scene, "reason"):
                print(f"   Game over reason: {next_scene.reason}")
        else:
            print("❌ FAILURE: No scene transition detected")

    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback

        traceback.print_exc()
    finally:
        pygame.quit()

    print("=== Test Complete ===")


if __name__ == "__main__":
    asyncio.run(test_game_over_client())

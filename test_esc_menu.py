#!/usr/bin/env python3

import os
import sys

import pygame

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from client.scenes.game_scene import GameScene
from client.utils.network_manager import NetworkManager


def test_esc_menu():
    """Test the ESC menu functionality without network connection"""
    pygame.init()
    screen = pygame.display.set_mode((1000, 600))
    pygame.display.set_caption("ESC Menu Test")
    clock = pygame.time.Clock()

    # Create a mock network manager
    network_manager = NetworkManager()
    network_manager.player_id = "test-player"

    # Create a minimal game state for testing
    mock_game_state = {
        "is_active": True,
        "is_paused": False,
        "lobby_id": "test-lobby",
        "wave_number": 1,
        "time_to_next_wave": 30.0,
        "players": {
            "test-player": {
                "player_id": "test-player",
                "name": "Test Player",
                "hero_type": "TANK",
                "position": {"x": 50, "y": 50},
                "health": 100,
                "max_health": 100,
                "resources": {
                    "wood": 50,
                    "stone": 30,
                    "wheat": 20,
                    "metal": 10,
                    "gold": 5,
                },
                "is_alive": True,
            }
        },
        "buildings": {},
        "enemies": {},
        "pings": {},
        "attack_effects": {},
        "map_data": [[{"type": "EMPTY", "explored_by": []}] * 50 for _ in range(50)],
    }

    try:
        game_scene = GameScene(screen, network_manager, mock_game_state)
        print("✅ GameScene created successfully!")
        print("Controls:")
        print("- Press ESC to open/close the menu")
        print("- Click 'Continue' to close menu")
        print("- Click 'Quit to Menu' to exit")
        print("- Press Q to quit test")

        running = True
        while running:
            dt = clock.tick(60) / 1000.0  # Delta time in seconds

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q:
                        running = False
                    else:
                        game_scene.handle_event(event)
                else:
                    game_scene.handle_event(event)

            # Check if scene wants to transition (quit to menu)
            next_scene = game_scene.get_next_scene()
            if next_scene:
                print("✅ ESC menu 'Quit to Menu' works!")
                running = False

            game_scene.update(dt)
            game_scene.render(screen)
            pygame.display.flip()

    except Exception as e:
        print(f"❌ Error creating or running GameScene: {e}")
        import traceback

        traceback.print_exc()
        return False

    pygame.quit()
    print("✅ ESC menu test completed successfully!")
    return True


if __name__ == "__main__":
    test_esc_menu()

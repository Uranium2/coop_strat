#!/usr/bin/env python3

"""
Test script to verify the building menu opens automatically when hero is selected
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from unittest.mock import Mock

import pygame

from client.scenes.game_scene import GameScene
from client.utils.network_manager import NetworkManager
from shared.models.game_models import Position


def test_building_menu_auto_open():
    """Test that building menu opens when hero is selected"""

    # Initialize pygame for testing
    pygame.init()
    screen = pygame.display.set_mode((800, 600))

    # Create mock network manager
    network_manager = Mock(spec=NetworkManager)
    network_manager.player_id = "test_player_123"

    # Create mock game state with a hero
    initial_game_state = {
        "lobby_id": "test_lobby",
        "is_active": True,
        "is_paused": False,
        "wave_number": 0,
        "time_to_next_wave": 60.0,
        "game_over_reason": "NONE",
        "map_data": [[0 for _ in range(50)] for _ in range(50)],
        "heroes": {
            "hero_1": {
                "id": "hero_1",
                "player_id": "test_player_123",
                "position": {"x": 10.0, "y": 10.0},
                "health": 100,
                "max_health": 100,
                "hero_type": "WARRIOR",
            }
        },
        "enemies": {},
        "buildings": {},
        "units": {},
        "players": {
            "test_player_123": {
                "id": "test_player_123",
                "name": "Test Player",
                "resources": {
                    "wood": 100,
                    "stone": 50,
                    "metal": 25,
                    "gold": 75,
                    "wheat": 40,
                },
            }
        },
        "pings": {},
        "attack_effects": {},
        "fog_of_war": [[True for _ in range(50)] for _ in range(50)],
    }

    # Create game scene
    game_scene = GameScene(screen, network_manager, initial_game_state)

    # Verify building menu is initially hidden
    assert not game_scene.building_menu.visible, (
        "Building menu should be initially hidden"
    )

    # Test clicking on hero (simulating left click)
    # Hero is at world position (10, 10), convert to screen coordinates
    hero_screen_x = 10 * 32 - game_scene.camera_x  # TILE_SIZE = 32
    hero_screen_y = 10 * 32 - game_scene.camera_y

    # Simulate left click on hero
    game_scene._handle_left_click((hero_screen_x, hero_screen_y))

    # Verify hero is selected
    assert game_scene.selected_entity is not None, "Hero should be selected"
    assert hasattr(game_scene.selected_entity, "hero_type"), (
        "Selected entity should be a hero"
    )

    # Verify building menu is now visible
    assert game_scene.building_menu.visible, (
        "Building menu should be visible after selecting hero"
    )

    # Test clicking on enemy (should hide building menu)
    # First add an enemy to the game state
    game_scene.game_state.enemies = {
        "enemy_1": Mock(position=Position(x=15.0, y=15.0), health=50)
    }

    # Click on different position (enemy location)
    enemy_screen_x = 15 * 32 - game_scene.camera_x
    enemy_screen_y = 15 * 32 - game_scene.camera_y
    game_scene._handle_left_click((enemy_screen_x, enemy_screen_y))

    # Verify building menu is hidden
    assert not game_scene.building_menu.visible, (
        "Building menu should be hidden when selecting non-hero"
    )

    # Test clicking on empty space (should hide building menu)
    game_scene._handle_left_click((hero_screen_x, hero_screen_y))  # Select hero again
    assert game_scene.building_menu.visible, (
        "Building menu should be visible after selecting hero again"
    )

    game_scene._handle_left_click((100, 100))  # Click on empty space
    assert not game_scene.building_menu.visible, (
        "Building menu should be hidden when clicking empty space"
    )

    print("✅ All building menu auto-open tests passed!")
    return True


if __name__ == "__main__":
    test_building_menu_auto_open()
    pygame.quit()

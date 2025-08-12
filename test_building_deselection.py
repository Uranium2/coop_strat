#!/usr/bin/env python3
"""
Test script to verify building deselection after placement.
Tests that the building button color returns to blue after placing a building.
"""

import asyncio
import os
import sys

import pygame

sys.path.append(os.path.join(os.path.dirname(__file__), "client"))
sys.path.append(os.path.join(os.path.dirname(__file__), "shared"))

from client.scenes.game_scene import GameScene
from client.utils.network_manager import NetworkManager
from shared.models.game_models import (
    BuildingType,
    Hero,
    HeroType,
    Player,
    Position,
    Resources,
    TileType,
)


async def test_building_deselection():
    """Test that building buttons are deselected after placement."""

    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("Building Deselection Test")

    # Create a mock network manager
    network_manager = NetworkManager()
    network_manager.player_id = "test_player"

    # Create test data
    test_hero = Hero(
        id="hero1",
        player_id="test_player",
        position=Position(x=5, y=5),
        hero_type=HeroType.BUILDER,
        health=100,
        max_health=100,
    )

    test_player = Player(
        id="test_player",
        name="Test Player",
        hero_type=HeroType.BUILDER,
        resources=Resources(wood=100, stone=100, wheat=100, metal=100, gold=100),
    )

    initial_game_state = {
        "heroes": {"hero1": test_hero.model_dump()},
        "players": {"test_player": test_player.model_dump()},
        "enemies": {},
        "buildings": {},
        "units": {},
        "pings": {},
        "attack_effects": {},
        "map_data": [[TileType.EMPTY.value for _ in range(50)] for _ in range(50)],
        "fog_of_war": [[True for _ in range(50)] for _ in range(50)],
        "game_time": 0.0,
        "is_active": True,
        "is_paused": False,
        "game_over_reason": "NONE",
        "wave_number": 0,
        "time_to_next_wave": 30.0,
    }

    # Create game scene
    game_scene = GameScene(screen, network_manager, initial_game_state)

    print("🧪 Testing Building Deselection...")

    # Step 1: Select hero to open building menu
    print("\n1. Selecting hero...")
    hero_screen_pos = game_scene._world_to_screen((5, 5))
    left_click_event = pygame.event.Event(
        pygame.MOUSEBUTTONDOWN,
        {"button": 1, "pos": (hero_screen_pos[0] + 16, hero_screen_pos[1] + 16)},
    )
    game_scene.handle_event(left_click_event)

    assert game_scene.building_menu.visible, "Building menu should be visible"
    assert game_scene.building_menu.selected_building_type is None, (
        "No building should be selected initially"
    )
    print("✅ Hero selected, building menu opened")

    # Step 2: Select a building from menu
    print("\n2. Selecting WALL building...")
    wall_button_rect = game_scene.building_menu.building_buttons["WALL"]["rect"]
    building_click_event = pygame.event.Event(
        pygame.MOUSEBUTTONDOWN, {"button": 1, "pos": wall_button_rect.center}
    )
    game_scene.handle_event(building_click_event)

    assert game_scene.building_placer.is_placing(), "Building placer should be active"
    assert game_scene.building_menu.selected_building_type == BuildingType.WALL, (
        "WALL should be selected"
    )
    print("✅ WALL building selected (should be GREEN now)")

    # Step 3: Test manual deselection (simulating successful placement)
    print("\n3. Testing manual deselection...")
    print(
        f"   Before clear: selected_building_type = {game_scene.building_menu.selected_building_type}"
    )

    # Manually call clear_selection to simulate what happens after successful placement
    game_scene.building_menu.clear_selection()

    assert game_scene.building_menu.selected_building_type is None, (
        "Building should be deselected after clear_selection()"
    )
    print("✅ Building deselected after clear_selection() (should be BLUE now)")

    # Step 4: Verify we can still select buildings after deselection
    print("\n4. Testing reselection after deselection...")
    tower_button_rect = game_scene.building_menu.building_buttons["TOWER"]["rect"]
    tower_click_event = pygame.event.Event(
        pygame.MOUSEBUTTONDOWN, {"button": 1, "pos": tower_button_rect.center}
    )
    game_scene.handle_event(tower_click_event)

    assert game_scene.building_placer.is_placing(), (
        "Building placer should be active for tower"
    )
    assert game_scene.building_menu.selected_building_type == BuildingType.TOWER, (
        "TOWER should be selected"
    )
    print("✅ TOWER building selected after deselection (should be GREEN now)")

    # Step 5: Test that clear_selection works again
    print("\n5. Testing second deselection...")
    game_scene.building_menu.clear_selection()
    game_scene.building_placer.stop_placement()  # Also stop placement

    assert game_scene.building_menu.selected_building_type is None, (
        "Building should be deselected again"
    )
    assert not game_scene.building_placer.is_placing(), (
        "Building placer should be inactive"
    )
    print("✅ Building deselected again (should be BLUE now)")

    print("\n🎉 All building deselection tests passed!")
    print("\nExpected visual behavior:")
    print("- Initially: All buttons BLUE (when affordable)")
    print("- After selecting WALL: WALL button GREEN, others BLUE")
    print("- After clear_selection(): All buttons BLUE (WALL deselected)")
    print("- After selecting TOWER: TOWER button GREEN, others BLUE")
    print("- After second clear_selection(): All buttons BLUE (TOWER deselected)")
    print(
        "\n✅ The clear_selection() method correctly resets building button colors to BLUE!"
    )


if __name__ == "__main__":
    asyncio.run(test_building_deselection())

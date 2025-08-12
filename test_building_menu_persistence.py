#!/usr/bin/env python3

import asyncio
import pygame
import sys
from unittest.mock import Mock

# Add the project root to the path
sys.path.insert(0, '/home/uranium/coop_strat')

from client.scenes.game_scene import GameScene
from client.utils.network_manager import NetworkManager
from shared.models.game_models import GameState, Hero, Player, Position, Resources, HeroType, TileType

async def test_building_menu_persistence():
    """Test that building menu stays open when hero is selected, even during building placement preview"""
    
    # Initialize pygame
    pygame.init()
    screen = pygame.display.set_mode((1000, 700))
    pygame.display.set_caption("Building Menu Persistence Test")
    
    # Create mock network manager
    network_manager = Mock(spec=NetworkManager)
    network_manager.player_id = "test_player"
    network_manager.send_game_action = Mock(return_value=asyncio.create_task(asyncio.sleep(0)))
    network_manager.register_handler = Mock()
    
    # Create test game state
    test_hero = Hero(
        id="hero1",
        position=Position(x=5, y=5),
        health=100,
        max_health=100,
        player_id="test_player",
        hero_type=HeroType.BUILDER
    )
    
    test_player = Player(
        id="test_player",
        name="Test Player", 
        hero_type=HeroType.BUILDER,
        resources=Resources(wood=100, stone=100, wheat=100, metal=100, gold=100)
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
        "time_to_next_wave": 30.0
    }
    
    # Create game scene
    game_scene = GameScene(screen, network_manager, initial_game_state)
    
    print("🧪 Testing Building Menu Persistence...")
    print(f"Initial building menu visible: {game_scene.building_menu.visible}")
    
    # Test 1: Select hero - building menu should open
    print("\n1. Testing hero selection...")
    hero_screen_pos = game_scene._world_to_screen((5, 5))
    left_click_event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {
        'button': 1, 
        'pos': (hero_screen_pos[0] + 16, hero_screen_pos[1] + 16)  # Center of hero tile
    })
    game_scene.handle_event(left_click_event)
    
    assert game_scene.selected_entity is not None, "Hero should be selected"
    assert hasattr(game_scene.selected_entity, "hero_type"), "Selected entity should be a hero"
    assert game_scene.building_menu.visible, "Building menu should be visible when hero is selected"
    print("✅ Hero selected, building menu opened")
    
    # Test 2: Click on building menu to select a building - menu should stay open
    print("\n2. Testing building selection from menu...")
    # Simulate clicking on the wall button in building menu
    wall_button_rect = game_scene.building_menu.building_buttons["WALL"]["rect"]
    building_click_event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {
        'button': 1,
        'pos': wall_button_rect.center
    })
    game_scene.handle_event(building_click_event)
    
    assert game_scene.building_placer.is_placing(), "Building placer should be active"
    assert game_scene.building_menu.visible, "Building menu should still be visible during placement preview"
    print("✅ Building selected, building menu remains open during preview")
    
    # Test 3: Right-click to cancel placement - menu should stay open
    print("\n3. Testing right-click cancellation...")
    right_click_event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {
        'button': 3,
        'pos': (500, 350)  # Somewhere in the middle of screen
    })
    game_scene.handle_event(right_click_event)
    
    assert not game_scene.building_placer.is_placing(), "Building placer should be inactive after right-click"
    assert game_scene.selected_entity is not None, "Hero should still be selected"
    assert game_scene.building_menu.visible, "Building menu should still be visible after cancelling placement"
    print("✅ Placement cancelled, building menu remains open")
    
    # Test 4: Select another building and place it - menu should stay open
    print("\n4. Testing building placement completion...")
    # Select tower from menu
    tower_button_rect = game_scene.building_menu.building_buttons["TOWER"]["rect"]
    tower_click_event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {
        'button': 1,
        'pos': tower_button_rect.center
    })
    game_scene.handle_event(tower_click_event)
    
    assert game_scene.building_placer.is_placing(), "Building placer should be active for tower"
    
    # Place the building with left click
    placement_click_event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {
        'button': 1,
        'pos': (400, 300)  # Valid placement location
    })
    game_scene.handle_event(placement_click_event)
    
    assert not game_scene.building_placer.is_placing(), "Building placer should be inactive after placement"
    assert game_scene.selected_entity is not None, "Hero should still be selected"
    assert game_scene.building_menu.visible, "Building menu should still be visible after placing building"
    print("✅ Building placed, building menu remains open")
    
    # Test 5: Right-click on empty space to deselect hero - menu should close
    print("\n5. Testing hero deselection...")
    deselect_click_event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {
        'button': 3,
        'pos': (600, 400)  # Empty space
    })
    game_scene.handle_event(deselect_click_event)
    
    assert game_scene.selected_entity is None, "Hero should be deselected"
    assert not game_scene.building_menu.visible, "Building menu should be hidden when hero is deselected"
    print("✅ Hero deselected, building menu closes")
    
    print("\n🎉 All tests passed! Building menu persistence works correctly.")
    
    # Clean up
    pygame.quit()

if __name__ == "__main__":
    asyncio.run(test_building_menu_persistence())
#!/usr/bin/env python3

"""
Debug script to test building menu and placement flow
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import pygame
from shared.models.game_models import Resources, BuildingType
from client.ui.building_menu import BuildingMenu
from client.ui.building_placer import BuildingPlacer

def test_building_menu_flow():
    """Test the building menu selection and placer workflow"""
    
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    
    # Create building menu
    building_menu = BuildingMenu(800, 600)
    building_placer = BuildingPlacer()
    
    # Create test resources
    resources = Resources(wood=100, stone=50, metal=25, gold=75, wheat=40)
    
    # Show building menu
    building_menu.show(resources)
    print("✅ Building menu visible:", building_menu.visible)
    
    # Test building button positions
    print("\n📍 Building button positions:")
    for building_type, button_info in building_menu.building_buttons.items():
        rect = button_info["rect"]
        can_afford = building_menu._can_afford_building(building_type)
        print(f"  {building_type}: {rect} - Can afford: {can_afford}")
    
    # Simulate clicking on first affordable building
    first_building = None
    for building_type, button_info in building_menu.building_buttons.items():
        if building_menu._can_afford_building(building_type):
            first_building = building_type
            break
    
    if first_building:
        print(f"\n🔧 Testing click on {first_building}")
        
        # Create a mock click event on the first building button
        button_rect = building_menu.building_buttons[first_building]["rect"]
        click_pos = (button_rect.centerx, button_rect.centery)
        
        # Create mock event
        class MockEvent:
            def __init__(self, pos, button=1):
                self.type = pygame.MOUSEBUTTONDOWN
                self.pos = pos
                self.button = button
        
        mock_event = MockEvent(click_pos)
        selected_building = building_menu.handle_event(mock_event)
        
        print(f"✅ Selected building: {selected_building}")
        print(f"✅ Building placer started: {building_placer.is_placing()}")
        
        if selected_building:
            # Start placement
            building_placer.start_placement(selected_building)
            print(f"✅ Building placer started: {building_placer.is_placing()}")
            print(f"✅ Building type: {building_placer.building_type}")
            
            # Test position update
            from shared.models.game_models import Position
            test_position = Position(x=100, y=100)  # Pixel coordinates
            
            # Create minimal game state for testing
            class MockGameState:
                def __init__(self):
                    self.buildings = {}
                    self.heroes = {}
                    self.units = {}
                    self.map_data = [[0 for _ in range(50)] for _ in range(50)]
            
            game_state = MockGameState()
            building_placer.update_position(test_position, game_state, "test_player")
            
            print(f"✅ Preview position: {building_placer.preview_position}")
            print(f"✅ Valid placement: {building_placer.is_valid_placement}")
            
            # Test getting placement info
            placement_info = building_placer.get_placement_info()
            if placement_info:
                building_type, position, is_valid = placement_info
                print(f"✅ Placement info: {building_type}, {position}, valid={is_valid}")
            
    else:
        print("❌ No affordable buildings found")
    
    pygame.quit()
    return True

if __name__ == "__main__":
    test_building_menu_flow()
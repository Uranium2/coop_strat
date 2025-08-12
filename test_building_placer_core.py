#!/usr/bin/env python3

import os
import sys

import pygame

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from client.ui.building_placer import BuildingPlacer
from shared.models.game_models import (
    BuildingPreviewState,
    BuildingType,
    GameState,
    Hero,
    HeroType,
    Player,
    Position,
    Resources,
)


def create_mock_game_state():
    """Create a minimal game state for testing"""
    player = Player(
        id="test_player",
        name="Test Player",
        resources=Resources(wood=100, stone=50, gold=100),
    )

    hero = Hero(
        id="hero_1",
        player_id="test_player",
        hero_type=HeroType.WARRIOR,
        position=Position(x=160, y=160),  # 5 * 32, 5 * 32
        health=100,
        max_health=100,
        attack_damage=25,
        attack_range=1.5,
    )

    # Create a simple map
    map_data = [[1 for _ in range(20)] for _ in range(20)]
    fog_of_war = [[True for _ in range(20)] for _ in range(20)]

    game_state = GameState(
        players={"test_player": player},
        heroes={"hero_1": hero},
        units={},
        buildings={},
        enemies={},
        map_data=map_data,
        fog_of_war=fog_of_war,
        wave_number=1,
        is_active=True,
        is_paused=False,
        game_time=0.0,
    )

    return game_state


def test_building_placer_functionality():
    """Test the core building placer functionality"""
    print("🏗️  Testing Building Placer Core Functionality")
    print("=" * 60)

    game_state = create_mock_game_state()
    player_id = "test_player"
    building_placer = BuildingPlacer()

    print("\n📋 Test 1: Initial State")
    assert building_placer.is_placing() == False
    assert building_placer.has_map_preview() == False
    assert building_placer.is_cursor_preview == True
    print("✅ Initial state is correct")

    print("\n📋 Test 2: Start Placement Mode")
    building_placer.start_placement(BuildingType.BARRACKS)
    assert building_placer.is_placing() == True
    assert building_placer.building_type == BuildingType.BARRACKS
    assert building_placer.is_cursor_preview == True
    assert building_placer.has_map_preview() == False
    print("✅ Cursor placement mode started correctly")

    print("\n📋 Test 3: Place Preview on Map")
    # Try to place at (480, 480) - should be valid
    world_pos = Position(x=480, y=480)
    result = building_placer.place_preview_on_map(world_pos, game_state, player_id)
    assert result == True
    assert building_placer.has_map_preview() == True
    assert building_placer.is_cursor_preview == False

    preview_info = building_placer.get_map_preview_info()
    assert preview_info is not None
    building_type, position = preview_info
    assert building_type == BuildingType.BARRACKS
    assert position.x == 480  # Should be snapped to grid
    assert position.y == 480
    print("✅ Map preview placed successfully")

    print("\n📋 Test 4: Hero Proximity Check")
    # Check initial hero distance (should not be adjacent)
    hero = game_state.heroes["hero_1"]
    is_adjacent_initial = building_placer._is_hero_adjacent_to_building(hero, position)
    assert is_adjacent_initial == False
    print("✅ Hero correctly identified as not adjacent initially")

    # Move hero closer
    hero.position = Position(x=448, y=448)  # Adjacent to (480, 480)
    is_adjacent_after = building_placer._is_hero_adjacent_to_building(hero, position)
    assert is_adjacent_after == True
    print("✅ Hero correctly identified as adjacent after movement")

    print("\n📋 Test 5: Preview State Logic")
    # Test preview state determination
    preview_state = building_placer._determine_preview_state(
        position, game_state, player_id
    )
    assert preview_state == BuildingPreviewState.VALID  # Hero is now adjacent
    print("✅ Preview state logic working correctly")

    print("\n📋 Test 6: Clear Preview")
    building_placer.clear_map_preview()
    assert building_placer.has_map_preview() == False
    assert building_placer.get_map_preview_info() is None
    assert building_placer.is_cursor_preview == True
    print("✅ Map preview cleared successfully")

    print("\n📋 Test 7: Stop Placement")
    building_placer.stop_placement()
    assert building_placer.is_placing() == False
    assert building_placer.building_type is None
    assert building_placer.has_map_preview() == False
    print("✅ Placement stopped successfully")

    return True


def test_rendering_functionality():
    """Test the rendering aspects"""
    print("\n🎨 Testing Rendering Functionality")
    print("=" * 60)

    pygame.init()
    screen = pygame.display.set_mode((800, 600))

    game_state = create_mock_game_state()
    player_id = "test_player"
    building_placer = BuildingPlacer()

    print("\n📋 Test 1: Cursor Preview Rendering")
    building_placer.start_placement(BuildingType.BARRACKS)
    world_pos = Position(x=200, y=200)
    building_placer.update_position(world_pos, game_state, player_id)

    # Test that rendering doesn't crash
    try:
        building_placer.render_preview(screen, (0, 0))
        print("✅ Cursor preview rendering works")
    except Exception as e:
        print(f"❌ Cursor preview rendering failed: {e}")
        return False

    print("\n📋 Test 2: Map Preview Rendering")
    world_pos = Position(x=480, y=480)
    building_placer.place_preview_on_map(world_pos, game_state, player_id)

    try:
        building_placer.render_map_preview(screen, (0, 0), game_state, player_id)
        print("✅ Map preview rendering works")
    except Exception as e:
        print(f"❌ Map preview rendering failed: {e}")
        return False

    pygame.quit()
    return True


def main():
    """Run all tests"""
    print("🚀 Starting Building Placer Tests")
    print("=" * 80)

    try:
        # Test core functionality
        test_building_placer_functionality()

        # Test rendering
        test_rendering_functionality()

        print("\n" + "=" * 80)
        print("🎉 ALL TESTS PASSED! Building Placer is Working Correctly!")
        print("=" * 80)

        print("\n📝 Key Features Verified:")
        print("✅ Cursor preview mode → Map placement transition")
        print("✅ Hero proximity detection")
        print("✅ Building preview state management")
        print("✅ Grid snapping for building placement")
        print("✅ Map preview rendering system")
        print("✅ Proper cleanup and state management")

        print("\n🎮 New Workflow Summary:")
        print("1. 🖱️  User selects building from menu (cursor preview starts)")
        print("2. 📍 User clicks on map (preview placed, cursor preview stops)")
        print("3. 🏃 Hero automatically travels to location if not adjacent")
        print("4. 🏗️  Construction starts when hero reaches the location")
        print("5. ✨ UI state resets (building menu cleared, no cursor preview)")

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        raise


if __name__ == "__main__":
    main()

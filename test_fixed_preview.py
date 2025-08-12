#!/usr/bin/env python3

import os
import sys

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from client.ui.building_placer import BuildingPlacer
from shared.models.game_models import BuildingType, Position


def test_fixed_preview():
    """Test that the building preview gets fixed to the map position"""

    placer = BuildingPlacer()

    print("🏗️ Testing Building Preview Behavior")
    print("=" * 50)

    # Start building placement
    placer.start_placement(BuildingType.WALL)
    print(f"1. Started placement - Cursor preview active: {placer.is_cursor_preview}")
    print(f"   Has map preview: {placer.has_map_preview()}")

    # Simulate clicking at a position (placing preview on map)
    click_position = Position(x=640.0, y=480.0)  # Some position on screen

    # Mock game state - minimal data needed
    class MockGameState:
        def __init__(self):
            self.heroes = {}
            self.buildings = {}
            self.map_data = [[0 for _ in range(100)] for _ in range(100)]

    game_state = MockGameState()
    player_id = "test_player"

    # Place preview on map (this happens when hero is not adjacent)
    success = placer.place_preview_on_map(click_position, game_state, player_id)

    print(f"2. Placed preview on map - Success: {success}")
    print(f"   Cursor preview active: {placer.is_cursor_preview}")
    print(f"   Has map preview: {placer.has_map_preview()}")

    if placer.has_map_preview():
        map_info = placer.get_map_preview_info()
        if map_info:
            building_type, position = map_info
            print(
                f"   Map preview: {building_type.value} at ({position.x}, {position.y})"
            )

    # Test clearing
    placer.clear_map_preview()
    print("3. Cleared map preview")
    print(f"   Has map preview: {placer.has_map_preview()}")

    # Test stop placement
    placer.stop_placement()
    print("4. Stopped placement")
    print(f"   Cursor preview active: {placer.is_cursor_preview}")
    print(f"   Has map preview: {placer.has_map_preview()}")


if __name__ == "__main__":
    test_fixed_preview()

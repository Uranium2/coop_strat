#!/usr/bin/env python3

import os
import sys

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


from map_editor import MapEditor
from shared.models.game_models import TileType


def create_test_map():
    """Create a simple test map and save it"""

    print("🗺️ Creating test map...")

    # Create a small test map
    width, height = 20, 15
    editor = MapEditor(width, height)

    # Create a simple pattern - border of stones, some resource patches
    for y in range(height):
        for x in range(width):
            if x == 0 or x == width - 1 or y == 0 or y == height - 1:
                # Border
                editor.map_data[y][x] = TileType.STONE
            elif 5 <= x <= 7 and 5 <= y <= 7:
                # Wood patch
                editor.map_data[y][x] = TileType.WOOD
            elif 12 <= x <= 14 and 3 <= y <= 5:
                # Metal patch
                editor.map_data[y][x] = TileType.METAL
            elif 3 <= x <= 5 and 10 <= y <= 12:
                # Wheat patch
                editor.map_data[y][x] = TileType.WHEAT
            elif x == 10 and y == 8:
                # Single gold tile
                editor.map_data[y][x] = TileType.GOLD
            else:
                # Empty space
                editor.map_data[y][x] = TileType.EMPTY

    # Save the test map
    editor.save_map()

    print("✅ Test map created!")

    # List all maps
    if os.path.exists("maps"):
        maps = [f for f in os.listdir("maps") if f.endswith(".json")]
        print(f"📂 Available maps ({len(maps)}):")
        for map_file in maps:
            print(f"   - {map_file}")


if __name__ == "__main__":
    create_test_map()

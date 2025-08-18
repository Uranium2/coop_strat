#!/usr/bin/env python3

from shared.constants.game_constants import TILE_SIZE


def test_building_rendering_coordinates():
    """Test that building rendering coordinates are converted correctly"""
    print("🧪 Testing building rendering coordinate conversion")

    # Example building at pixel coordinates (like from your log)
    building_pixel_x = 3072.0
    building_pixel_y = 3104.0

    print(f"📍 Building at pixels ({building_pixel_x}, {building_pixel_y})")

    # Convert to tile coordinates (what _world_to_screen expects)
    building_tile_x = building_pixel_x // TILE_SIZE
    building_tile_y = building_pixel_y // TILE_SIZE

    print(f"📍 Building converted to tiles ({building_tile_x}, {building_tile_y})")

    # Simulate _world_to_screen conversion with camera at origin
    camera_x = 0
    camera_y = 0

    # OLD (buggy) way - passing pixels to _world_to_screen
    old_screen_x = int(building_pixel_x * TILE_SIZE - camera_x)
    old_screen_y = int(building_pixel_y * TILE_SIZE - camera_y)

    # NEW (fixed) way - passing tiles to _world_to_screen
    new_screen_x = int(building_tile_x * TILE_SIZE - camera_x)
    new_screen_y = int(building_tile_y * TILE_SIZE - camera_y)

    print(f"\n❌ OLD (BUGGY) screen position: ({old_screen_x}, {old_screen_y})")
    print(f"✅ NEW (FIXED) screen position: ({new_screen_x}, {new_screen_y})")

    # Check visibility (typical screen size 1920x1080)
    screen_width = 1920
    screen_height = 1080

    old_visible = (
        -TILE_SIZE < old_screen_x < screen_width
        and -TILE_SIZE < old_screen_y < screen_height
    )
    new_visible = (
        -TILE_SIZE < new_screen_x < screen_width
        and -TILE_SIZE < new_screen_y < screen_height
    )

    print(f"\n📺 Screen bounds: {screen_width}x{screen_height}")
    print(f"❌ OLD method visible: {old_visible}")
    print(f"✅ NEW method visible: {new_visible}")

    print("\n🔍 ANALYSIS:")
    print(f"   Building is at tile ({building_tile_x}, {building_tile_y})")
    print(
        f"   With camera at origin, building should render at ({new_screen_x}, {new_screen_y})"
    )
    print(f"   Building is {'VISIBLE' if new_visible else 'NOT VISIBLE'} on screen")


if __name__ == "__main__":
    test_building_rendering_coordinates()

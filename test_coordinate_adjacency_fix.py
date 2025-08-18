#!/usr/bin/env python3

import math

from shared.constants.game_constants import TILE_SIZE


def test_coordinate_conversion():
    """Test that adjacency calculation works with proper coordinate conversion"""
    print("🧪 Testing coordinate adjacency fix")

    # Simulate the scenario from the bug report
    hero_tile_x = 95
    hero_tile_y = 97

    # Building position in pixels (from pending_build)
    building_pixel_x = 3040  # 95 * 32
    building_pixel_y = 3104  # 97 * 32

    print(f"📍 Hero at tile ({hero_tile_x}, {hero_tile_y})")
    print(f"📍 Building at pixels ({building_pixel_x}, {building_pixel_y})")

    # OLD (buggy) way - treating pixels as tiles
    print("\n❌ OLD (BUGGY) METHOD:")
    buggy_building_tile_x = building_pixel_x  # Wrong: treating pixels as tiles
    buggy_building_tile_y = building_pixel_y
    buggy_distance = math.sqrt(
        (hero_tile_x - buggy_building_tile_x) ** 2
        + (hero_tile_y - buggy_building_tile_y) ** 2
    )
    print(
        f"   Buggy distance: {buggy_distance:.2f} (comparing tile {hero_tile_x},{hero_tile_y} vs 'tile' {buggy_building_tile_x},{buggy_building_tile_y})"
    )
    print(f"   Adjacent? {buggy_distance <= 1.8}")

    # NEW (fixed) way - convert pixels to tiles
    print("\n✅ NEW (FIXED) METHOD:")
    correct_building_tile_x = int(building_pixel_x // TILE_SIZE)
    correct_building_tile_y = int(building_pixel_y // TILE_SIZE)

    print(
        f"   Building pixel ({building_pixel_x}, {building_pixel_y}) -> tile ({correct_building_tile_x}, {correct_building_tile_y})"
    )

    # Check adjacency for a 2x2 building
    building_size = (2, 2)
    min_distance = float("inf")

    for bx in range(
        correct_building_tile_x, correct_building_tile_x + building_size[0]
    ):
        for by in range(
            correct_building_tile_y, correct_building_tile_y + building_size[1]
        ):
            distance = math.sqrt((hero_tile_x - bx) ** 2 + (hero_tile_y - by) ** 2)
            min_distance = min(min_distance, distance)
            print(f"   Distance to building tile ({bx}, {by}): {distance:.2f}")

    print(f"   Minimum distance: {min_distance:.2f}")
    print(f"   Adjacent? {min_distance <= 1.8}")

    # Test actual adjacency - hero should be adjacent to a building at the same tile
    print("\n🔍 ANALYSIS:")
    print(f"   Hero is at tile ({hero_tile_x}, {hero_tile_y})")
    print(
        f"   Building (2x2) occupies tiles ({correct_building_tile_x}, {correct_building_tile_y}) to ({correct_building_tile_x + 1}, {correct_building_tile_y + 1})"
    )
    print(
        f"   Hero is {'ADJACENT' if min_distance <= 1.8 else 'NOT ADJACENT'} to the building"
    )

    if (
        correct_building_tile_x == hero_tile_x
        and correct_building_tile_y == hero_tile_y
    ):
        print(
            "   ✅ Hero is at the SAME tile as building's top-left corner - should be adjacent!"
        )
    elif (
        abs(correct_building_tile_x - hero_tile_x) <= 1
        and abs(correct_building_tile_y - hero_tile_y) <= 1
    ):
        print("   ✅ Hero is within 1 tile of building - should be adjacent!")
    else:
        print("   ❌ Hero is more than 1 tile away from building")


if __name__ == "__main__":
    test_coordinate_conversion()

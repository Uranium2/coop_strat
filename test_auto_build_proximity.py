#!/usr/bin/env python3

import math
import os
import sys

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from shared.constants.game_constants import BUILDING_TYPES
from shared.models.game_models import Hero, HeroType, Position


def test_proximity_detection():
    """Test the hero proximity detection logic for auto-build"""

    # Create a test hero
    hero = Hero(
        id="test_hero",
        player_id="test_player",
        hero_type=HeroType.BUILDER,
        position=Position(x=10, y=10),  # Hero at tile (10, 10)
        health=100,
        max_health=100,
    )

    # Test building at tile (12, 10) - 2 tiles to the right
    building_type = "WALL"
    building_pos = {"x": 12, "y": 10}

    print("🏗️ Testing proximity detection")
    print(f"👤 Hero at tile ({hero.position.x}, {hero.position.y})")
    print(
        f"🏢 Building '{building_type}' at tile ({building_pos['x']}, {building_pos['y']})"
    )

    # Get building size
    building_info = BUILDING_TYPES.get(building_type)
    if not building_info:
        print("❌ Building type not found!")
        return
    size = building_info["size"]
    print(f"📏 Building size: {size}")

    # Test proximity at different hero positions
    test_positions = [
        (10, 10, "Far away (2 tiles)"),
        (11, 10, "Adjacent (1 tile)"),
        (12, 10, "On building"),
        (13, 10, "On building"),
        (14, 10, "Just past building"),
        (11, 9, "Diagonal adjacent"),
        (11, 11, "Diagonal adjacent"),
    ]

    for test_x, test_y, description in test_positions:
        # Update hero position
        hero.position.x = test_x
        hero.position.y = test_y

        # Apply the same logic as in the game scene
        hero_tile_x = int(hero.position.x)
        hero_tile_y = int(hero.position.y)
        building_tile_x = building_pos["x"]
        building_tile_y = building_pos["y"]

        # Check if hero touches any border of the building area
        is_adjacent = False
        min_distance = float("inf")

        for bx in range(building_tile_x, building_tile_x + size[0]):
            for by in range(building_tile_y, building_tile_y + size[1]):
                distance = math.sqrt((hero_tile_x - bx) ** 2 + (hero_tile_y - by) ** 2)
                min_distance = min(min_distance, distance)
                if distance <= 1.5:  # Hero touches building border
                    is_adjacent = True
                    break
            if is_adjacent:
                break

        status = "✅ ADJACENT" if is_adjacent else "❌ NOT ADJACENT"
        print(
            f"  Hero at ({test_x}, {test_y}) - {description}: {status} (min distance: {min_distance:.2f})"
        )


if __name__ == "__main__":
    test_proximity_detection()

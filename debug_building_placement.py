#!/usr/bin/env python3

import asyncio
import time
import uuid
from typing import Dict

import pygame

from shared.models.game_models import (
    Hero,
    Player,
    Position,
    BuildingType,
    Resources,
    HeroType,
)
from server.services.game_manager import GameManager


async def test_building_placement():
    print("🔧 Testing Building Placement Debug")
    print("=" * 50)

    # Create test player
    player = Player(
        id="test_player",
        name="Test Player",
        hero_type=HeroType.BUILDER,
        resources=Resources(wood=100, stone=100, wheat=100, metal=100, gold=100),
    )

    # Create game manager with players
    players = {"test_player": player}
    game_manager = GameManager("test_lobby", players)

    # The GameManager automatically spawns heroes, so get the existing hero
    hero = None
    for h in game_manager.game_state.heroes.values():
        if h.player_id == "test_player":
            hero = h
            break

    if not hero:
        print("❌ No hero found after GameManager initialization!")
        return

    print(f"📍 Auto-spawned Hero Position: ({hero.position.x}, {hero.position.y})")

    # NOW set the hero to our desired position
    hero.position = Position(x=5.0, y=5.0)
    print(f"📍 Modified Hero Position: ({hero.position.x}, {hero.position.y})")

    # Test Case 1: Try to build right next to hero (should work)
    build_position = Position(x=6 * 32, y=5 * 32)  # Convert to pixel coordinates
    print(f"🏗️ Attempting to build FARM at pixel position ({build_position.x}, {build_position.y})")
    print(f"🏗️ This is tile position ({build_position.x // 32}, {build_position.y // 32})")
    print(f"🏗️ Hero at tile ({hero.position.x}, {hero.position.y}), building at tile ({build_position.x // 32}, {build_position.y // 32})")
    print(f"🏗️ Expected distance from hero (5,5) to building tile (6,5): {((5 - 6) ** 2 + (5 - 5) ** 2) ** 0.5:.2f}")

    result = game_manager.build_structure("test_player", BuildingType.FARM, build_position)
    print(f"✅ Build result: {result}")

    if result:
        print("🎉 Building placement worked!")
        return

    print("❌ Building failed! Let's try placing hero at exact building location")
    # Move hero to the exact building location
    hero.position = Position(x=6.0, y=5.0)
    print(f"🚶 Moved hero to ({hero.position.x}, {hero.position.y})")
    print(f"🏗️ Expected distance from hero (6,5) to building tile (6,5): {((6 - 6) ** 2 + (5 - 5) ** 2) ** 0.5:.2f}")
    
    result2 = game_manager.build_structure("test_player", BuildingType.FARM, build_position)
    print(f"✅ Build result with hero at building position: {result2}")
    
    if result2:
        print("🎉 Building placement worked after moving hero!")
        return

    print("🤔 Still failing! Let's test with hero at each individual building tile")
    # Test each tile of the 2x2 building
    building_tile_x = int(build_position.x // 32)
    building_tile_y = int(build_position.y // 32)
    
    for bx in range(building_tile_x, building_tile_x + 2):
        for by in range(building_tile_y, building_tile_y + 2):
            hero.position = Position(x=float(bx), y=float(by))
            print(f"🚶 Testing with hero at tile ({bx}, {by})")
            result3 = game_manager.build_structure("test_player", BuildingType.FARM, build_position)
            print(f"✅ Build result with hero at ({bx}, {by}): {result3}")
            if result3:
                print(f"🎉 Building placement worked with hero at ({bx}, {by})!")
                return


if __name__ == "__main__":
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    
    try:
        asyncio.run(test_building_placement())
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        pygame.quit()
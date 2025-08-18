#!/usr/bin/env python3

"""
Test the coordinate conversion fix for building placement.
Verifies that client sends pixel coordinates to server correctly.
"""

import asyncio
import sys
import os
import logging

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from shared.models.game_models import Hero, GameState, Player, Resources, Position, BuildingType, HeroType, TileType, GameOverReason
from server.services.game_manager import GameManager
from shared.constants.game_constants import TILE_SIZE

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_coordinate_conversion():
    """Test that coordinates are converted correctly"""
    print("🧪 Testing coordinate conversion fix")
    
    # Create game manager with test state
    game_manager = GameManager()
    
    # Create a player with resources
    player_id = "test_player"
    player = Player(
        id=player_id,
        name="Test Player",
        hero_type=HeroType.BUILDER,
        resources=Resources(
            wood=100, stone=100, wheat=100, 
            metal=100, gold=100
        ),
        is_connected=True
    )
    
    # Create a hero for the player
    hero = Hero(
        id=f"hero_{player_id}",
        player_id=player_id,
        hero_type=HeroType.BUILDER,
        position=Position(x=160.0, y=160.0),  # Pixel coordinates (5*32, 5*32)
        health=100,
        max_health=100
    )
    
    # Create a simple 10x10 map with grass
    map_data = [[TileType.GRASS for _ in range(10)] for _ in range(10)]
    fog_of_war = [[False for _ in range(10)] for _ in range(10)]
    
    game_state = GameState(
        lobby_id="test_lobby",
        players={player_id: player},
        heroes={hero.id: hero},
        buildings={},
        units={},
        enemies={},
        pings={},
        attack_effects={},
        map_data=map_data,
        fog_of_war=fog_of_war,
        game_time=0.0,
        is_active=True,
        is_paused=False,
        game_over_reason=GameOverReason.NONE,
        wave_number=1,
        next_wave_time=30.0,
        time_to_next_wave=30.0
    )
    game_manager.game_state = game_state
    
    # Test scenario: Hero at tile (5, 5), want to build at tile (6, 5)
    hero_tile_x, hero_tile_y = 5, 5
    build_tile_x, build_tile_y = 6, 5
    
    # Convert to pixel coordinates (what client should send)
    hero_pixel_x = hero_tile_x * TILE_SIZE  # 5 * 32 = 160
    hero_pixel_y = hero_tile_y * TILE_SIZE  # 5 * 32 = 160
    build_pixel_x = build_tile_x * TILE_SIZE  # 6 * 32 = 192
    build_pixel_y = build_tile_y * TILE_SIZE  # 6 * 32 = 160
    
    print(f"📍 Hero tile position: ({hero_tile_x}, {hero_tile_y})")
    print(f"📍 Hero pixel position: ({hero_pixel_x}, {hero_pixel_y})")
    print(f"🏗️ Build tile position: ({build_tile_x}, {build_tile_y})")
    print(f"🏗️ Build pixel position: ({build_pixel_x}, {build_pixel_y})")
    
    # Test building placement with pixel coordinates
    build_position = Position(x=float(build_pixel_x), y=float(build_pixel_y))
    
    print(f"\n🔧 Testing build_structure with pixel coordinates ({build_pixel_x}, {build_pixel_y})")
    success = game_manager.build_structure(player_id, BuildingType.FARM, build_position)
    
    if success:
        print("✅ Building placement SUCCESS!")
        # Check if building was actually created
        if game_manager.game_state.buildings:
            building = next(iter(game_manager.game_state.buildings.values()))
            print(f"🏢 Building created at: ({building.position.x}, {building.position.y})")
            
            # Verify the building is at the expected tile
            expected_tile_x = int(building.position.x // TILE_SIZE)
            expected_tile_y = int(building.position.y // TILE_SIZE)
            print(f"🗺️ Building tile position: ({expected_tile_x}, {expected_tile_y})")
            
            if expected_tile_x == build_tile_x and expected_tile_y == build_tile_y:
                print("✅ Building placed at correct tile!")
            else:
                print(f"❌ Building placed at wrong tile! Expected ({build_tile_x}, {build_tile_y})")
        else:
            print("❌ No building found in game state!")
    else:
        print("❌ Building placement FAILED!")
        
        # Let's check what went wrong by testing the validation methods
        print("\n🔍 Debugging validation:")
        
        # Check if position is valid
        from shared.constants.game_constants import BUILDING_TYPES
        building_info = BUILDING_TYPES.get(BuildingType.FARM)
        if building_info:
            is_valid = game_manager._is_valid_build_position(build_position, building_info["size"])
            print(f"📏 Position valid: {is_valid}")
            
            # Check adjacency
            is_adjacent = game_manager._is_hero_adjacent_to_build_location(player_id, build_position, building_info["size"])
            print(f"🤝 Hero adjacent: {is_adjacent}")
            
            # Check resources
            can_afford = game_manager._can_afford(player, building_info["cost"])
            print(f"💰 Can afford: {can_afford}")

if __name__ == "__main__":
    asyncio.run(test_coordinate_conversion())
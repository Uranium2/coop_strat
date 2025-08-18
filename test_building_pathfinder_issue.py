#!/usr/bin/env python3
"""Test script to debug building placement issues with the new pathfinder"""

import asyncio
import os
import sys
import time
import math

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from server.services.game_manager import GameManager
from server.services.lobby_manager import LobbyManager
from shared.models.game_models import (
    GameState, Player, Hero, Resources, Position, 
    BuildingType, HeroType
)
from shared.constants.game_constants import BUILDING_TYPES


async def test_building_placement_issue():
    """Test the building placement workflow to identify the pathfinder issue"""
    print("🔧 Testing building placement issue with new pathfinder")
    
    # Create game manager with a simple setup
    lobby_id = "test_lobby"
    players = {"test_player": {"name": "Test Player", "hero_type": "BUILDER"}}
    game_manager = GameManager(lobby_id, players)
    
    # Create a simple game state
    player_id = "test_player"
    hero_id = "test_hero"
    
    # Add player
    player = Player(
        id=player_id,
        name="Test Player",
        resources=Resources(wood=100, stone=100, wheat=100, metal=100, gold=100),
        hero_type=HeroType.BUILDER
    )
    game_manager.game_state.players[player_id] = player
    
    # Add hero at starting position
    hero = Hero(
        id=hero_id,
        player_id=player_id,
        hero_type=HeroType.BUILDER,
        position=Position(x=10.0, y=10.0),  # Starting position
        health=150,
        max_health=150,
        path_waypoints=[]
    )
    game_manager.game_state.heroes[hero_id] = hero
    
    print(f"📍 Initial hero position: ({hero.position.x:.2f}, {hero.position.y:.2f})")
    
    # Step 1: Move hero to a target position where we want to build
    target_position = Position(x=15, y=15)  # Target position in tile coordinates
    print(f"🎯 Moving hero to target: ({target_position.x}, {target_position.y})")
    
    # Move hero (simulating the client's move command)
    move_success = game_manager.move_hero(player_id, target_position)
    print(f"Move command result: {move_success}")
    
    if not move_success:
        print("❌ Hero movement failed")
        return
    
    # Step 2: Simulate game loop to move hero to target
    print("🚶 Simulating hero movement...")
    max_iterations = 100
    iteration = 0
    
    while iteration < max_iterations:
        # Update hero movements (like game loop does)
        game_manager._update_hero_movements(0.1)  # 0.1 second timestep
        
        # Check if hero reached target (no more targets/paths)
        if hero_id not in game_manager.hero_targets:
            print(f"✅ Hero reached target after {iteration} iterations")
            break
            
        iteration += 1
        if iteration % 10 == 0:
            print(f"   Iteration {iteration}: Hero at ({hero.position.x:.2f}, {hero.position.y:.2f})")
    
    if iteration >= max_iterations:
        print(f"⚠️ Hero didn't reach target after {max_iterations} iterations")
        print(f"   Final position: ({hero.position.x:.2f}, {hero.position.y:.2f})")
        print(f"   Target position: ({target_position.x}, {target_position.y})")
    
    final_pos = hero.position
    print(f"📍 Final hero position: ({final_pos.x:.2f}, {final_pos.y:.2f})")
    
    # Step 3: Test building placement at target location
    building_position = Position(x=15, y=15)  # Same as target, tile coordinates
    print(f"🏗️ Attempting to build at: ({building_position.x}, {building_position.y})")
    
    # Test adjacency check (what the server does)
    building_info = BUILDING_TYPES.get(BuildingType.BARRACKS)
    if not building_info:
        print("❌ Could not find building info for BARRACKS")
        return
    
    size = building_info["size"]  # Should be (3, 2)
    print(f"Building size: {size}")
    
    # Manual adjacency check (replicating server logic)
    hero_tile_x = int(hero.position.x)
    hero_tile_y = int(hero.position.y)
    building_tile_x = int(building_position.x)
    building_tile_y = int(building_position.y)
    
    print(f"Hero tile position: ({hero_tile_x}, {hero_tile_y})")
    print(f"Building tile position: ({building_tile_x}, {building_tile_y})")
    print(f"Building covers tiles: ({building_tile_x}, {building_tile_y}) to ({building_tile_x + size[0] - 1}, {building_tile_y + size[1] - 1})")
    
    # Check adjacency manually
    is_adjacent = False
    min_distance = float("inf")
    
    for bx in range(building_tile_x, building_tile_x + size[0]):
        for by in range(building_tile_y, building_tile_y + size[1]):
            distance = math.sqrt((hero_tile_x - bx) ** 2 + (hero_tile_y - by) ** 2)
            min_distance = min(min_distance, distance)
            print(f"   Distance to building tile ({bx}, {by}): {distance:.2f}")
            if distance <= 1.5:  # Adjacency threshold
                is_adjacent = True
    
    print(f"Minimum distance to building: {min_distance:.2f}")
    print(f"Is hero adjacent? {is_adjacent} (threshold: 1.5)")
    
    # Step 4: Try actual building placement
    build_success = game_manager.build_structure(player_id, BuildingType.BARRACKS, building_position)
    print(f"Building placement result: {build_success}")
    
    if not build_success:
        print("❌ Building placement failed")
        print("Likely reasons:")
        print(f"   - Hero not adjacent (distance: {min_distance:.2f})")
        print(f"   - Invalid build position")
        print(f"   - Insufficient resources")
    else:
        print("✅ Building placement succeeded!")
    
    # Step 5: Test the issue by moving hero slightly closer
    if not is_adjacent:
        print("\n🔧 Testing with hero moved closer...")
        # Move hero to a position that should definitely be adjacent
        for test_pos in [
            (building_tile_x - 1, building_tile_y),     # Left of building
            (building_tile_x + size[0], building_tile_y), # Right of building
            (building_tile_x, building_tile_y - 1),     # Above building
            (building_tile_x, building_tile_y + size[1]) # Below building
        ]:
            hero.position.x = float(test_pos[0])
            hero.position.y = float(test_pos[1])
            
            # Test adjacency
            test_distance = math.sqrt((test_pos[0] - building_tile_x) ** 2 + (test_pos[1] - building_tile_y) ** 2)
            test_adjacent = game_manager._is_hero_adjacent_to_build_location(
                player_id, building_position, size
            )
            
            print(f"   Hero at ({test_pos[0]}, {test_pos[1]}): distance={test_distance:.2f}, adjacent={test_adjacent}")
            
            if test_adjacent:
                print(f"   ✅ Hero is adjacent at position ({test_pos[0]}, {test_pos[1]})")
                break


if __name__ == "__main__":
    asyncio.run(test_building_placement_issue())
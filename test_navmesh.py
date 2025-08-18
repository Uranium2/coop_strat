#!/usr/bin/env python3
"""
Test script for NavMesh pathfinding system.
Run this to test the new NavMesh pathfinding implementation.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server.services.navmesh import NavMeshPathfinder, NavMesh
from shared.models.game_models import Position, TileType


def create_test_map():
    """Create a simple test map with obstacles"""
    # 10x10 map with some obstacles
    tile_map = []
    for y in range(10):
        row = []
        for x in range(10):
            if (x == 3 and 2 <= y <= 6) or (x == 7 and 3 <= y <= 7):
                # Vertical walls
                row.append(TileType.WALL)
            elif (y == 4 and 4 <= x <= 6):
                # Horizontal wall
                row.append(TileType.WOOD)
            else:
                row.append(TileType.EMPTY)
        tile_map.append(row)
    
    return tile_map


def visualize_path(tile_map, path, start, goal):
    """Visualize the path on the map"""
    print("\nPath visualization:")
    print("Legend: . = Empty, # = Wall/Wood, S = Start, G = Goal, * = Path")
    
    # Create visualization grid
    vis_map = []
    for y in range(len(tile_map)):
        row = []
        for x in range(len(tile_map[0])):
            if tile_map[y][x] in [TileType.WALL, TileType.WOOD]:
                row.append('#')
            else:
                row.append('.')
        vis_map.append(row)
    
    # Mark path
    for pos in path:
        x, y = int(pos.x), int(pos.y)
        if 0 <= x < len(tile_map[0]) and 0 <= y < len(tile_map):
            if vis_map[y][x] == '.':
                vis_map[y][x] = '*'
    
    # Mark start and goal
    start_x, start_y = int(start.x), int(start.y)
    goal_x, goal_y = int(goal.x), int(goal.y)
    vis_map[start_y][start_x] = 'S'
    vis_map[goal_y][goal_x] = 'G'
    
    # Print the map
    for row in vis_map:
        print(' '.join(row))


def test_navmesh_pathfinding():
    """Test the NavMesh pathfinding system"""
    print("Testing NavMesh Pathfinding System")
    print("==================================")
    
    # Create test map
    tile_map = create_test_map()
    
    print("Test map layout:")
    for y, row in enumerate(tile_map):
        line = ""
        for x, tile in enumerate(row):
            if tile in [TileType.WALL, TileType.WOOD]:
                line += "# "
            else:
                line += ". "
        print(f"{y}: {line}")
    
    # Initialize NavMesh pathfinder
    pathfinder = NavMeshPathfinder(10, 10)
    
    try:
        # Generate NavMesh
        print("\nGenerating NavMesh...")
        pathfinder.generate_navmesh(tile_map)
        
        # Print generated polygons
        print(f"Generated {len(pathfinder.navmesh.polygons)} polygons")
        for poly_id, polygon in pathfinder.navmesh.polygons.items():
            print(f"  Polygon {poly_id}: center at ({polygon.center.x:.1f}, {polygon.center.y:.1f})")
        
        # Test pathfinding scenarios
        test_cases = [
            (Position(x=1.0, y=1.0), Position(x=8.0, y=8.0), "Diagonal across obstacles"),
            (Position(x=0.5, y=0.5), Position(x=9.5, y=9.5), "Corner to corner"),
            (Position(x=2.0, y=4.0), Position(x=8.0, y=4.0), "Around vertical wall"),
            (Position(x=5.0, y=2.0), Position(x=5.0, y=7.0), "Around horizontal wall"),
        ]
        
        for i, (start, goal, description) in enumerate(test_cases, 1):
            print(f"\nTest {i}: {description}")
            print(f"From ({start.x}, {start.y}) to ({goal.x}, {goal.y})")
            
            path = pathfinder.find_path(start, goal)
            
            if path:
                print(f"✓ Path found with {len(path)} waypoints:")
                for j, pos in enumerate(path):
                    print(f"  {j}: ({pos.x:.2f}, {pos.y:.2f})")
                
                # Calculate path length
                total_length = 0.0
                for j in range(1, len(path)):
                    dx = path[j].x - path[j-1].x
                    dy = path[j].y - path[j-1].y
                    total_length += (dx*dx + dy*dy)**0.5
                print(f"  Total path length: {total_length:.2f}")
                
                visualize_path(tile_map, path, start, goal)
            else:
                print("✗ No path found")
        
    except Exception as e:
        print(f"Error during testing: {e}")
        import traceback
        traceback.print_exc()


def test_polygon_generation():
    """Test polygon generation specifically"""
    print("\nTesting Polygon Generation")
    print("=========================")
    
    # Simple 5x5 map with one obstacle
    simple_map = []
    for y in range(5):
        row = []
        for x in range(5):
            if x == 2 and y == 2:
                row.append(TileType.WALL)
            else:
                row.append(TileType.EMPTY)
        tile_map.append(row)
    
    navmesh = NavMesh(5, 5)
    navmesh.generate_from_tile_map(simple_map)
    
    print(f"Generated {len(navmesh.polygons)} polygons for simple 5x5 map with 1 obstacle")
    for poly_id, polygon in navmesh.polygons.items():
        print(f"  Polygon {poly_id}:")
        print(f"    Center: ({polygon.center.x:.1f}, {polygon.center.y:.1f})")
        print(f"    Vertices: {[(v.x, v.y) for v in polygon.vertices]}")
        print(f"    Neighbors: {polygon.neighbors}")


if __name__ == "__main__":
    print("NavMesh Pathfinding Test Suite")
    print("==============================\n")
    
    test_polygon_generation()
    test_navmesh_pathfinding()
    
    print("\nTesting completed!")
#!/usr/bin/env python3
"""
Co-op Strategy RTS Map Editor Demo
==================================

This script demonstrates the map editor functionality and shows how to:
1. Create custom maps
2. Save maps to files  
3. Load existing maps

Usage:
    python3 map_demo.py [options]

Options:
    --editor         Launch the interactive map editor
    --edit MAP       Launch the editor with a specific map loaded
    --create-demo    Create a demo map programmatically  
    --list-maps      List all available maps
    --info MAP       Show info about a specific map
"""

import sys
import os
import argparse

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def show_available_maps():
    """List all available maps"""
    from server.services.map_loader import MapLoader
    
    loader = MapLoader()
    maps = loader.list_available_maps()
    
    if not maps:
        print("📂 No custom maps found in maps/ directory")
        print("   Use --create-demo to create a sample map")
        print("   Use --editor to launch the interactive editor")
        return
        
    print(f"📂 Available Custom Maps ({len(maps)}):")
    print("=" * 50)
    
    for map_file in maps:
        info = loader.get_map_info(map_file)
        if info:
            print(f"📄 {info['name']}")
            print(f"   File: {info['filename']}")
            print(f"   Size: {info['width']}x{info['height']} tiles")
            print(f"   Created: {info['created'][:19]}")  # Remove microseconds
            print()

def show_map_info(map_filename):
    """Show detailed info about a specific map"""
    from server.services.map_loader import MapLoader
    
    loader = MapLoader()
    map_data = loader.load_map(map_filename)
    
    if not map_data:
        print(f"❌ Failed to load map: {map_filename}")
        return
        
    metadata = map_data.get("metadata", {})
    tiles = map_data.get("map_data", [])
    
    print(f"🗺️ Map: {metadata.get('name', map_filename)}")
    print("=" * 50)
    print(f"File: {map_filename}")
    print(f"Size: {len(tiles[0]) if tiles else 0}x{len(tiles)} tiles")
    print(f"Version: {metadata.get('version', 'Unknown')}")
    print(f"Created: {metadata.get('created', 'Unknown')}")
    print()
    
    # Analyze tile distribution
    if tiles:
        from shared.models.game_models import TileType
        tile_counts = {}
        
        for row in tiles:
            for tile in row:
                if tile in tile_counts:
                    tile_counts[tile] += 1
                else:
                    tile_counts[tile] = 1
        
        print("📊 Tile Distribution:")
        total_tiles = sum(tile_counts.values())
        for tile_type, count in sorted(tile_counts.items()):
            percentage = (count / total_tiles) * 100
            print(f"   {tile_type.value:8s}: {count:4d} tiles ({percentage:5.1f}%)")

def create_demo_map():
    """Create a demo map programmatically"""
    from map_editor import MapEditor
    from shared.models.game_models import TileType
    
    print("🗺️ Creating demo map...")
    
    # Create a 30x20 demo map
    width, height = 30, 20
    editor = MapEditor(width, height)
    
    # Create an interesting pattern
    for y in range(height):
        for x in range(width):
            # Border
            if x == 0 or x == width-1 or y == 0 or y == height-1:
                editor.map_data[y][x] = TileType.STONE
            # Central clearing
            elif 12 <= x <= 17 and 8 <= y <= 11:
                editor.map_data[y][x] = TileType.EMPTY
            # Resource patches
            elif 5 <= x <= 9 and 5 <= y <= 8:
                editor.map_data[y][x] = TileType.WOOD
            elif 20 <= x <= 24 and 5 <= y <= 8:
                editor.map_data[y][x] = TileType.WOOD
            elif 5 <= x <= 9 and 12 <= y <= 15:
                editor.map_data[y][x] = TileType.STONE
            elif 20 <= x <= 24 and 12 <= y <= 15:
                editor.map_data[y][x] = TileType.STONE
            # Wheat fields
            elif 10 <= x <= 12 and 3 <= y <= 5:
                editor.map_data[y][x] = TileType.WHEAT
            elif 17 <= x <= 19 and 3 <= y <= 5:
                editor.map_data[y][x] = TileType.WHEAT
            # Metal deposits
            elif x in [8, 21] and y in [10, 11]:
                editor.map_data[y][x] = TileType.METAL
            # Gold spots
            elif (x == 15 and y == 5) or (x == 15 and y == 14):
                editor.map_data[y][x] = TileType.GOLD
            else:
                editor.map_data[y][x] = TileType.EMPTY
    
    # Override metadata name
    original_save = editor.save_map
    def custom_save():
        editor.save_map()
        # Find the saved file and rename it
        import glob
        import shutil
        latest_map = max(glob.glob("maps/custom_map_*.json"))
        demo_path = "maps/demo_map.json"
        if os.path.exists(demo_path):
            os.remove(demo_path)
        shutil.move(latest_map, demo_path)
        print(f"✅ Demo map saved as: demo_map.json")
    
    custom_save()

def launch_editor_with_map(map_filename=None):
    """Launch the interactive map editor, optionally with a specific map loaded"""
    from map_editor import MapEditor
    
    print("🚀 Launching Map Editor...")
    if map_filename:
        print(f"📂 Loading map: {map_filename}")
    
    print("📋 Controls:")
    print("   - WASD/Arrow keys: Move camera")
    print("   - 1-6: Select tile type")
    print("   - Left click: Place tile")
    print("   - Right click: Clear tile")
    print("   - G: Toggle grid")
    print("   - Ctrl+S: Save map")
    print("   - Ctrl+O: Load map")
    print("   - Ctrl+N: New map")
    print("   - ESC: Exit")
    print()
    
    editor = MapEditor()
    
    # Load specific map if provided
    if map_filename:
        editor.load_specific_map(map_filename)
    
    editor.run()

def launch_editor():
    """Launch the interactive map editor"""
    launch_editor_with_map()

def main():
    parser = argparse.ArgumentParser(
        description="Co-op Strategy RTS Map Editor Demo",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument("--editor", action="store_true", help="Launch interactive map editor")
    parser.add_argument("--edit", metavar="MAP", help="Launch editor with specific map loaded")
    parser.add_argument("--create-demo", action="store_true", help="Create a demo map")
    parser.add_argument("--list-maps", action="store_true", help="List available maps")
    parser.add_argument("--info", metavar="MAP", help="Show info about a specific map")
    
    args = parser.parse_args()
    
    # Create maps directory if it doesn't exist
    os.makedirs("maps", exist_ok=True)
    
    if args.editor:
        launch_editor()
    elif args.edit:
        launch_editor_with_map(args.edit)
    elif args.create_demo:
        create_demo_map()
    elif args.list_maps:
        show_available_maps()
    elif args.info:
        show_map_info(args.info)
    else:
        # Default: show help and available maps
        parser.print_help()
        print()
        show_available_maps()

if __name__ == "__main__":
    main()
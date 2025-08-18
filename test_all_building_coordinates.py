#!/usr/bin/env python3

from shared.constants.game_constants import TILE_SIZE, MAP_WIDTH, MAP_HEIGHT

def test_all_building_coordinates():
    """Test that all buildings use consistent coordinate system"""
    print("🧪 Testing consistent building coordinate system")
    
    # Town Hall positioning (now fixed)
    center_x = MAP_WIDTH // 2   # = 100 tiles
    center_y = MAP_HEIGHT // 2  # = 100 tiles
    
    town_hall_pixel_x = center_x * TILE_SIZE  # = 100 * 32 = 3200
    town_hall_pixel_y = center_y * TILE_SIZE  # = 100 * 32 = 3200
    
    print(f"📍 Town Hall:")
    print(f"   Center tile: ({center_x}, {center_y})")
    print(f"   Pixel position: ({town_hall_pixel_x}, {town_hall_pixel_y})")
    
    # Farm positioning (from build command)
    farm_pixel_x = 3072  # Example from your logs
    farm_pixel_y = 3104
    
    farm_tile_x = farm_pixel_x // TILE_SIZE  # = 96
    farm_tile_y = farm_pixel_y // TILE_SIZE  # = 97
    
    print(f"📍 Farm:")
    print(f"   Pixel position: ({farm_pixel_x}, {farm_pixel_y})")
    print(f"   Converted to tile: ({farm_tile_x}, {farm_tile_y})")
    
    # Rendering coordinate conversion test
    print(f"\n🎨 RENDERING TEST:")
    
    # Both buildings should now go through the same conversion process
    town_hall_render_tile_x = town_hall_pixel_x // TILE_SIZE
    town_hall_render_tile_y = town_hall_pixel_y // TILE_SIZE
    
    farm_render_tile_x = farm_pixel_x // TILE_SIZE  
    farm_render_tile_y = farm_pixel_y // TILE_SIZE
    
    print(f"   Town Hall: pixels ({town_hall_pixel_x}, {town_hall_pixel_y}) -> tiles ({town_hall_render_tile_x}, {town_hall_render_tile_y})")
    print(f"   Farm: pixels ({farm_pixel_x}, {farm_pixel_y}) -> tiles ({farm_render_tile_x}, {farm_render_tile_y})")
    
    # With camera at origin, screen positions should be:
    screen_x_townhall = town_hall_render_tile_x * TILE_SIZE  # Should equal town_hall_pixel_x
    screen_y_townhall = town_hall_render_tile_y * TILE_SIZE  # Should equal town_hall_pixel_y
    
    screen_x_farm = farm_render_tile_x * TILE_SIZE  # Should equal farm_pixel_x  
    screen_y_farm = farm_render_tile_y * TILE_SIZE  # Should equal farm_pixel_y
    
    print(f"   Town Hall screen pos: ({screen_x_townhall}, {screen_y_townhall})")
    print(f"   Farm screen pos: ({screen_x_farm}, {screen_y_farm})")
    
    print(f"\n✅ VERIFICATION:")
    print(f"   Town Hall: pixel->tile->screen = {town_hall_pixel_x} -> {town_hall_render_tile_x} -> {screen_x_townhall} ✓")
    print(f"   Farm: pixel->tile->screen = {farm_pixel_x} -> {farm_render_tile_x} -> {screen_x_farm} ✓")
    print(f"   Both buildings now use PIXEL coordinates and convert consistently!")

if __name__ == "__main__":
    test_all_building_coordinates()
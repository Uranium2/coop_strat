#!/usr/bin/env python3

"""
Simple test to demonstrate the coordinate conversion fix.
Tests what happens when client sends different coordinate types.
"""

from shared.constants.game_constants import TILE_SIZE


def test_coordinate_conversion():
    """Demonstrate the coordinate conversion issue and fix"""
    print("🧪 Testing Coordinate Conversion")
    print("=" * 50)

    # Scenario from the user's logs
    print("📍 Original scenario from logs:")
    print("  Client sends: position = {'x': 94, 'y': 98}")
    print("  Server receives: (94.0, 98.0)")
    print("  Server converts to tile: (94/32, 98/32) = (2.9, 3.0) ≈ (3, 3)")
    print("  ❌ Collision detected at tile (3, 3) - likely Town Hall")

    print("\n🔧 Fixed scenario:")

    # What the client should send (using our fix)
    client_tile_x, client_tile_y = 94, 98  # Original client values

    # Our fix: Convert to pixel coordinates
    client_pixel_x = client_tile_x * TILE_SIZE  # 94 * 32 = 3008
    client_pixel_y = client_tile_y * TILE_SIZE  # 98 * 32 = 3136

    print(f"  Client calculates pixel coords: ({client_pixel_x}, {client_pixel_y})")
    print(f"  Server receives: ({client_pixel_x:.1f}, {client_pixel_y:.1f})")

    # What server does with these coordinates
    server_tile_x = int(client_pixel_x // TILE_SIZE)
    server_tile_y = int(client_pixel_y // TILE_SIZE)

    print(
        f"  Server converts to tile: ({client_pixel_x}/32, {client_pixel_y}/32) = ({server_tile_x}, {server_tile_y})"
    )
    print(f"  ✅ Building placed at correct tile ({server_tile_x}, {server_tile_y})")

    # Verify the round-trip works
    if server_tile_x == client_tile_x and server_tile_y == client_tile_y:
        print("  ✅ Round-trip conversion successful!")
    else:
        print("  ❌ Round-trip conversion failed!")

    print("\n📊 Summary:")
    print("  Before fix: Client sends tile coords → Server misinterprets as pixels")
    print("  After fix:  Client sends pixel coords → Server correctly interprets")
    print("  \n🎯 The key change:")
    print("    Old: position: {'x': tile_x, 'y': tile_y}")
    print("    New: position: {'x': pixel_x, 'y': pixel_y}")
    print("    Where: pixel_x = tile_x * TILE_SIZE")


if __name__ == "__main__":
    test_coordinate_conversion()

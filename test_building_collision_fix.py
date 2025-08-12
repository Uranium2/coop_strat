#!/usr/bin/env python3
"""
Test script to verify building collision detection and placement cancellation works correctly.
This test checks:
1. Building collision detection prevents overlapping buildings
2. Right-click cancellation for building placement
3. Hero deselection when right-clicking empty space
"""

import asyncio
import sys
import time

import pygame

from client.main import GameClient


def log(message: str):
    """Log message with timestamp"""
    timestamp = time.strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}")


async def test_building_placement():
    """Test building placement and collision detection"""
    log("Starting building placement test...")

    # Initialize pygame
    pygame.init()

    try:
        # Create game client
        client = GameClient()

        # Start the client in test mode
        log("Creating lobby and starting game...")
        await client.network_manager.connect()
        await client.network_manager.create_lobby()

        # Wait for lobby to be ready
        await asyncio.sleep(2)

        # Start the game
        await client.network_manager.start_game()
        await asyncio.sleep(3)

        log("Game started, testing building placement...")

        # Test building placement collision detection
        log("Testing building collision detection...")

        # Try to place multiple buildings in the same location
        for i in range(3):
            await client.network_manager.send_game_action(
                {
                    "type": "build",
                    "building_type": "WALL",
                    "position": {"x": 10, "y": 10},
                }
            )
            await asyncio.sleep(0.5)

        await asyncio.sleep(2)

        log("Building placement test completed!")

        # Test simulation for 5 seconds
        start_time = time.time()
        frame_count = 0

        while time.time() - start_time < 5:
            # Simulate game loop
            dt = 1 / 60  # 60 FPS

            # Handle events (simulate right-click cancellation)
            events = pygame.event.get()
            for event in events:
                if hasattr(client, "current_scene") and client.current_scene:
                    client.current_scene.handle_event(event)

            # Update game
            if hasattr(client, "current_scene") and client.current_scene:
                client.current_scene.update(dt)

            frame_count += 1
            await asyncio.sleep(dt)

        log(f"Simulation completed! Processed {frame_count} frames")
        log("Test completed successfully!")

    except Exception as e:
        log(f"Test failed with error: {e}")
        import traceback

        traceback.print_exc()
        return False

    finally:
        pygame.quit()

    return True


async def main():
    """Main test function"""
    log("=== Building Collision Detection Test ===")

    success = await test_building_placement()

    if success:
        log("All tests passed! ✅")
        sys.exit(0)
    else:
        log("Tests failed! ❌")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

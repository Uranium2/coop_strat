#!/usr/bin/env python3
import sys

# Add project root to Python path
sys.path.insert(0, "/home/uranium/coop_strat")

import asyncio

import pygame

from client.scenes.menu_scene import MenuScene
from client.utils.network_manager import NetworkManager


async def main():
    print("Testing actual MenuScene...")

    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("MenuScene Test")
    clock = pygame.time.Clock()

    try:
        # Create network manager and menu scene
        network_manager = NetworkManager()
        scene = MenuScene(screen, network_manager)
        print("✓ MenuScene created successfully")
    except Exception as e:
        print(f"✗ Failed to create MenuScene: {e}")
        import traceback

        traceback.print_exc()
        return

    running = True
    frame_count = 0

    print("Starting game loop...")
    try:
        while running and frame_count < 300:  # 5 seconds at 60fps
            dt = clock.tick(60) / 1000.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                scene.handle_event(event)

            scene.update(dt)

            # Clear screen and render
            screen.fill((0, 0, 0))
            scene.render(screen)
            pygame.display.flip()

            frame_count += 1
            if frame_count % 60 == 0:
                print(f"Frame {frame_count}")

            await asyncio.sleep(0)

        print("✓ MenuScene rendering test completed")

    except Exception as e:
        print(f"✗ Error during rendering: {e}")
        import traceback

        traceback.print_exc()
    finally:
        pygame.quit()


if __name__ == "__main__":
    asyncio.run(main())

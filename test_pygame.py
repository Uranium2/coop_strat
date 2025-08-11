#!/usr/bin/env python3

import pygame

print("Testing basic pygame functionality...")

try:
    pygame.init()
    print("✓ pygame.init() successful")

    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("Pygame Test")
    print("✓ Display mode set successfully")

    clock = pygame.time.Clock()
    running = True
    frame_count = 0

    print("Starting render loop...")
    while running and frame_count < 60:  # Run for 60 frames max
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Fill screen with different colors to test rendering
        if frame_count < 20:
            screen.fill((255, 0, 0))  # Red
        elif frame_count < 40:
            screen.fill((0, 255, 0))  # Green
        else:
            screen.fill((0, 0, 255))  # Blue

        pygame.display.flip()
        clock.tick(60)
        frame_count += 1

        if frame_count % 20 == 0:
            print(f"Frame {frame_count}")

    print("✓ Rendering test completed successfully")

except Exception as e:
    print(f"✗ Error: {e}")
    import traceback

    traceback.print_exc()
finally:
    pygame.quit()
    print("✓ pygame.quit() successful")

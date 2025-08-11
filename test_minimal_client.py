#!/usr/bin/env python3
import asyncio

import pygame


# Test minimal client with menu
class TestMenuScene:
    def __init__(self, screen):
        self.screen = screen
        self.font = pygame.font.Font(None, 36)

    def handle_event(self, event):
        pass

    def update(self, dt):
        pass

    def render(self, screen):
        screen.fill((50, 50, 50))  # Dark gray

        # Render title
        title = self.font.render("Test Menu", True, (255, 255, 255))
        title_rect = title.get_rect(center=(screen.get_width() // 2, 150))
        screen.blit(title, title_rect)

        # Render button
        button_rect = pygame.Rect(350, 300, 100, 50)
        pygame.draw.rect(screen, (100, 100, 100), button_rect)
        pygame.draw.rect(screen, (255, 255, 255), button_rect, 2)

        button_text = self.font.render("Test", True, (255, 255, 255))
        button_text_rect = button_text.get_rect(center=button_rect.center)
        screen.blit(button_text, button_text_rect)


async def main():
    print("Starting minimal client test...")

    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("Minimal Client Test")
    clock = pygame.time.Clock()

    scene = TestMenuScene(screen)
    running = True
    frame_count = 0

    print("Starting game loop...")
    while running and frame_count < 300:  # 5 seconds at 60fps
        dt = clock.tick(60) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            scene.handle_event(event)

        scene.update(dt)
        scene.render(screen)
        pygame.display.flip()

        frame_count += 1
        if frame_count % 60 == 0:
            print(f"Frame {frame_count}")

        await asyncio.sleep(0)

    pygame.quit()
    print("✓ Minimal client test completed")


if __name__ == "__main__":
    asyncio.run(main())

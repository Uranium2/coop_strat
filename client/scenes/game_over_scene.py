import logging

import pygame

from client.utils.network_manager import NetworkManager
from shared.constants.game_constants import COLORS

logger = logging.getLogger(__name__)


class GameOverScene:
    def __init__(
        self,
        screen: pygame.Surface,
        network_manager: NetworkManager,
        reason: str = "TOWN_HALL_DESTROYED",
    ):
        self.screen = screen
        self.network_manager = network_manager
        self.reason = reason
        self.font = pygame.font.Font(None, 72)
        self.medium_font = pygame.font.Font(None, 48)
        self.small_font = pygame.font.Font(None, 36)
        self.next_scene = None

        logger.info(f"GameOverScene initialized with reason: {reason}")

        # Define buttons
        self.buttons = {
            "return_to_menu": pygame.Rect(400, 400, 300, 60),
            "quit": pygame.Rect(400, 480, 300, 60),
        }

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()

            if self.buttons["return_to_menu"].collidepoint(mouse_pos):
                logger.info("Return to menu button clicked")
                from client.scenes.menu_scene import MenuScene

                self.next_scene = MenuScene(self.screen, self.network_manager)

            elif self.buttons["quit"].collidepoint(mouse_pos):
                logger.info("Quit button clicked")
                pygame.quit()
                exit()

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                # ESC key returns to menu
                from client.scenes.menu_scene import MenuScene

                self.next_scene = MenuScene(self.screen, self.network_manager)

    def update(self, dt):
        # No updates needed for static game over screen
        pass

    def render(self, screen):
        # Clear screen with dark background
        screen.fill((20, 20, 20))

        # Get screen dimensions
        screen_width = screen.get_width()
        screen_height = screen.get_height()

        # Main title
        if self.reason == "TOWN_HALL_DESTROYED":
            title_text = "DEFEAT!"
            subtitle_text = "Your Town Hall has been destroyed"
            title_color = COLORS["RED"]
        elif self.reason == "VICTORY":
            title_text = "VICTORY!"
            subtitle_text = "You have successfully defended your town"
            title_color = COLORS["GREEN"]
        else:
            title_text = "GAME OVER"
            subtitle_text = "The game has ended"
            title_color = COLORS["WHITE"]

        # Render title
        title_surface = self.font.render(title_text, True, title_color)
        title_rect = title_surface.get_rect(center=(screen_width // 2, 200))
        screen.blit(title_surface, title_rect)

        # Render subtitle
        subtitle_surface = self.medium_font.render(subtitle_text, True, COLORS["WHITE"])
        subtitle_rect = subtitle_surface.get_rect(center=(screen_width // 2, 280))
        screen.blit(subtitle_surface, subtitle_rect)

        # Render buttons
        for button_name, button_rect in self.buttons.items():
            mouse_pos = pygame.mouse.get_pos()
            is_hovered = button_rect.collidepoint(mouse_pos)

            # Button background
            button_color = COLORS["BLUE"] if is_hovered else COLORS["GRAY"]
            pygame.draw.rect(screen, button_color, button_rect)
            pygame.draw.rect(screen, COLORS["WHITE"], button_rect, 2)

            # Button text
            if button_name == "return_to_menu":
                button_text = "Return to Menu"
            elif button_name == "quit":
                button_text = "Quit Game"
            else:
                button_text = button_name.replace("_", " ").title()

            text_surface = self.small_font.render(button_text, True, COLORS["WHITE"])
            text_rect = text_surface.get_rect(center=button_rect.center)
            screen.blit(text_surface, text_rect)

        # Instructions
        instruction_text = "Press ESC or click 'Return to Menu' to go back"
        instruction_surface = self.small_font.render(
            instruction_text, True, COLORS["GRAY"]
        )
        instruction_rect = instruction_surface.get_rect(
            center=(screen_width // 2, screen_height - 50)
        )
        screen.blit(instruction_surface, instruction_rect)

    def get_next_scene(self):
        return self.next_scene

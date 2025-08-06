import pygame
from shared.constants.game_constants import COLORS
from shared.models.game_models import Resources

class ResourcePanel:
    def __init__(self, x: int, y: int, width: int, height: int):
        self.rect = pygame.Rect(x, y, width, height)
        self.font = pygame.font.Font(None, 20)
        
    def render(self, screen: pygame.Surface, resources: Resources):
        pygame.draw.rect(screen, COLORS["BLACK"], self.rect)
        pygame.draw.rect(screen, COLORS["WHITE"], self.rect, 2)
        
        resource_texts = [
            f"Wood: {resources.wood}",
            f"Stone: {resources.stone}",
            f"Wheat: {resources.wheat}",
            f"Metal: {resources.metal}",
            f"Gold: {resources.gold}"
        ]
        
        y_offset = 5
        for i, text in enumerate(resource_texts):
            if i < 3:
                x_pos = self.rect.x + 5
                y_pos = self.rect.y + y_offset + (i * 15)
            else:
                x_pos = self.rect.x + 140
                y_pos = self.rect.y + y_offset + ((i - 3) * 15)
            
            text_surface = self.font.render(text, True, COLORS["WHITE"])
            screen.blit(text_surface, (x_pos, y_pos))
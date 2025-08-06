import pygame
from typing import Union
from shared.constants.game_constants import COLORS
from shared.models.game_models import Hero, Building

class SelectionPanel:
    def __init__(self, x: int, y: int, width: int, height: int):
        self.rect = pygame.Rect(x, y, width, height)
        self.font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 18)
        
    def render(self, screen: pygame.Surface, selected_entity: Union[Hero, Building]):
        pygame.draw.rect(screen, COLORS["BLACK"], self.rect)
        pygame.draw.rect(screen, COLORS["WHITE"], self.rect, 2)
        
        if hasattr(selected_entity, 'hero_type'):
            self._render_hero_info(screen, selected_entity)
        elif hasattr(selected_entity, 'building_type'):
            self._render_building_info(screen, selected_entity)
    
    def _render_hero_info(self, screen: pygame.Surface, hero: Hero):
        title = self.font.render(f"Hero: {hero.hero_type}", True, COLORS["WHITE"])
        screen.blit(title, (self.rect.x + 5, self.rect.y + 5))
        
        health_text = f"Health: {hero.health}/{hero.max_health}"
        health_surface = self.small_font.render(health_text, True, COLORS["WHITE"])
        screen.blit(health_surface, (self.rect.x + 5, self.rect.y + 30))
        
        # pos_text = f"Position: ({hero.position.x}, {hero.position.y})"
        # pos_surface = self.small_font.render(pos_text, True, COLORS["WHITE"])
        # screen.blit(pos_surface, (self.rect.x + 5, self.rect.y + 50))
    
    def _render_building_info(self, screen: pygame.Surface, building: Building):
        title = self.font.render(f"Building: {building.building_type}", True, COLORS["WHITE"])
        screen.blit(title, (self.rect.x + 5, self.rect.y + 5))
        
        health_text = f"Health: {building.health}/{building.max_health}"
        health_surface = self.small_font.render(health_text, True, COLORS["WHITE"])
        screen.blit(health_surface, (self.rect.x + 5, self.rect.y + 30))
        
        pos_text = f"Position: ({building.position.x}, {building.position.y})"
        pos_surface = self.small_font.render(pos_text, True, COLORS["WHITE"])
        screen.blit(pos_surface, (self.rect.x + 5, self.rect.y + 50))
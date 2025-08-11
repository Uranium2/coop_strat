import pygame
from typing import Union

from shared.constants.game_constants import COLORS, TILE_SIZE
from shared.models.game_models import Building, Enemy, Hero, Unit


class HealthBarRenderer:
    def __init__(self):
        self.bar_height = 4
        self.bar_offset_y = -8  # Pixels above the entity
    
    def draw_health_bar(self, screen: pygame.Surface, entity: Union[Hero, Unit, Enemy, Building], 
                       camera_x: float, camera_y: float):
        """Draw health bar above an entity"""
        if entity.health <= 0:
            return
        
        # Calculate screen position
        screen_x = entity.position.x * TILE_SIZE - camera_x
        screen_y = entity.position.y * TILE_SIZE - camera_y
        
        # Determine entity width for bar sizing
        if hasattr(entity, 'size'):  # Building
            entity_width = entity.size[0] * TILE_SIZE
        else:  # Hero, Unit, Enemy
            entity_width = TILE_SIZE
        
        # Health bar dimensions
        bar_width = entity_width
        bar_x = screen_x
        bar_y = screen_y + self.bar_offset_y
        
        # Don't draw if off screen (with some margin)
        if (bar_x + bar_width < -50 or bar_x > screen.get_width() + 50 or
            bar_y + self.bar_height < -50 or bar_y > screen.get_height() + 50):
            return
        
        # Background (dark red for missing health)
        pygame.draw.rect(screen, COLORS["DARK_GRAY"], 
                        (bar_x, bar_y, bar_width, self.bar_height))
        
        # Health fill (green)
        health_percentage = entity.health / entity.max_health
        fill_width = int(bar_width * health_percentage)
        
        # Color based on health percentage
        if health_percentage > 0.6:
            health_color = COLORS["GREEN"]
        elif health_percentage > 0.3:
            health_color = COLORS["YELLOW"]
        else:
            health_color = COLORS["RED"]
        
        if fill_width > 0:
            pygame.draw.rect(screen, health_color, 
                           (bar_x, bar_y, fill_width, self.bar_height))
        
        # Border
        pygame.draw.rect(screen, COLORS["WHITE"], 
                        (bar_x, bar_y, bar_width, self.bar_height), 1)
    
    def draw_mana_bar(self, screen: pygame.Surface, hero: Hero, 
                     camera_x: float, camera_y: float):
        """Draw mana bar below health bar for heroes"""
        if hero.health <= 0:
            return
        
        # Calculate screen position
        screen_x = hero.position.x * TILE_SIZE - camera_x
        screen_y = hero.position.y * TILE_SIZE - camera_y
        
        # Mana bar dimensions (below health bar)
        bar_width = TILE_SIZE
        bar_x = screen_x
        bar_y = screen_y + self.bar_offset_y + self.bar_height + 2
        
        # Don't draw if off screen
        if (bar_x + bar_width < -50 or bar_x > screen.get_width() + 50 or
            bar_y + self.bar_height < -50 or bar_y > screen.get_height() + 50):
            return
        
        # Background
        pygame.draw.rect(screen, COLORS["DARK_GRAY"], 
                        (bar_x, bar_y, bar_width, self.bar_height))
        
        # Mana fill (blue)
        mana_percentage = hero.mana / hero.max_mana
        fill_width = int(bar_width * mana_percentage)
        
        if fill_width > 0:
            pygame.draw.rect(screen, COLORS["BLUE"], 
                           (bar_x, bar_y, fill_width, self.bar_height))
        
        # Border
        pygame.draw.rect(screen, COLORS["WHITE"], 
                        (bar_x, bar_y, bar_width, self.bar_height), 1)
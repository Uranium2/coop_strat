import pygame
import pygame.gfxdraw
import math
from typing import Tuple, Optional
from shared.models.game_models import PingType

class RadialPingMenu:
    def __init__(self):
        self.is_active = False
        self.center_pos = (0, 0)
        self.radius = 80
        self.inner_radius = 20
        
        # Define ping types and their positions (in radians)
        self.ping_options = [
            (PingType.ATTENTION, 0, "Attention", (255, 255, 0)),      # Top (0 radians)
            (PingType.DANGER, math.pi/2, "Danger", (255, 0, 0)),      # Right (π/2 radians)
            (PingType.HELP, math.pi, "Help", (0, 255, 0)),            # Bottom (π radians)
            (PingType.MOVE_HERE, 3*math.pi/2, "Move", (0, 150, 255))  # Left (3π/2 radians)
        ]
        
        self.hovered_ping = None
        
        # Font for labels
        pygame.font.init()
        self.font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 18)
    
    def activate(self, pos: Tuple[int, int]):
        """Activate the radial menu at the given position"""
        self.is_active = True
        self.center_pos = pos
        self.hovered_ping = None
    
    def deactivate(self):
        """Deactivate the radial menu"""
        self.is_active = False
        self.hovered_ping = None
    
    def update_hover(self, mouse_pos: Tuple[int, int]) -> Optional[PingType]:
        """Update which ping option is being hovered based on direction from center"""
        if not self.is_active:
            return None
        
        # Calculate offset from center
        dx = mouse_pos[0] - self.center_pos[0]
        dy = mouse_pos[1] - self.center_pos[1]
        
        # If mouse is too close to center (dead zone), no selection
        distance = math.sqrt(dx*dx + dy*dy)
        if distance < self.inner_radius:
            self.hovered_ping = None
            return None
        
        # Calculate angle from center (0 = top, clockwise)
        # Adjust coordinates so 0 degrees is straight up
        angle = math.atan2(dx, -dy)  # -dy because screen Y is inverted
        if angle < 0:
            angle += 2 * math.pi
        
        # Convert to degrees for easier understanding
        angle_degrees = math.degrees(angle)
        
        # Determine which ping based on angle zones (each zone is 90 degrees)
        # Top: 315-45 degrees (or 315-360 and 0-45)
        # Right: 45-135 degrees  
        # Bottom: 135-225 degrees
        # Left: 225-315 degrees
        
        if angle_degrees >= 315 or angle_degrees < 45:
            # Top - Attention (Yellow)
            selected_ping = PingType.ATTENTION
        elif 45 <= angle_degrees < 135:
            # Right - Danger (Red)
            selected_ping = PingType.DANGER  
        elif 135 <= angle_degrees < 225:
            # Bottom - Help (Green)
            selected_ping = PingType.HELP
        else:  # 225 <= angle_degrees < 315
            # Left - Move Here (Blue)
            selected_ping = PingType.MOVE_HERE
        
        self.hovered_ping = selected_ping
        return selected_ping
    
    def get_selected_ping(self, mouse_pos: Tuple[int, int]) -> Optional[PingType]:
        """Get the selected ping type based on mouse direction from center"""
        return self.update_hover(mouse_pos)
    
    def draw(self, screen: pygame.Surface):
        """Draw the radial ping menu"""
        if not self.is_active:
            return
        
        center_x, center_y = self.center_pos
        
        # Create a transparent surface for the menu
        menu_surface = pygame.Surface((self.radius * 2 + 40, self.radius * 2 + 40), pygame.SRCALPHA)
        menu_rect = menu_surface.get_rect(center=self.center_pos)
        
        # Draw outer circle (background)
        pygame.draw.circle(menu_surface, (0, 0, 0, 100), 
                         (menu_surface.get_width()//2, menu_surface.get_height()//2), 
                         self.radius)
        
        # Draw directional zone highlights if hovered
        if self.hovered_ping:
            # Get the color for the hovered ping
            hovered_color = None
            for ping_type, angle, label, color in self.ping_options:
                if ping_type == self.hovered_ping:
                    hovered_color = color
                    break
            
            if hovered_color:
                # Draw a sector highlight for the selected direction
                menu_center = (menu_surface.get_width()//2, menu_surface.get_height()//2)
                
                # Create a larger transparent surface for the sector
                sector_surface = pygame.Surface((self.radius * 2 + 40, self.radius * 2 + 40), pygame.SRCALPHA)
                
                # Draw sector based on hovered ping type (90-degree sectors)
                if self.hovered_ping == PingType.ATTENTION:  # Top
                    start_angle = 315
                    end_angle = 45
                elif self.hovered_ping == PingType.DANGER:  # Right  
                    start_angle = 45
                    end_angle = 135
                elif self.hovered_ping == PingType.HELP:  # Bottom
                    start_angle = 135
                    end_angle = 225
                else:  # PingType.MOVE_HERE - Left
                    start_angle = 225
                    end_angle = 315
                
                # Draw the sector highlight (simplified - just draw lines)
                pygame.draw.circle(sector_surface, (*hovered_color, 60), menu_center, self.radius)
                screen.blit(sector_surface, menu_rect)
        
        # Draw inner circle (dead zone)
        pygame.draw.circle(menu_surface, (50, 50, 50, 150), 
                         (menu_surface.get_width()//2, menu_surface.get_height()//2), 
                         self.inner_radius)
        
        # Draw ping option sectors
        for ping_type, angle, label, color in self.ping_options:
            # Calculate position for this ping option
            sector_x = center_x + math.cos(angle - math.pi/2) * (self.radius * 0.7)
            sector_y = center_y + math.sin(angle - math.pi/2) * (self.radius * 0.7)
            
            # Highlight if hovered
            if self.hovered_ping == ping_type:
                # Draw highlight circle
                highlight_surface = pygame.Surface((60, 60), pygame.SRCALPHA)
                pygame.draw.circle(highlight_surface, (*color, 100), (30, 30), 28)
                screen.blit(highlight_surface, (sector_x - 30, sector_y - 30))
            
            # Draw ping icon/circle
            pygame.draw.circle(screen, color, (int(sector_x), int(sector_y)), 15)
            pygame.draw.circle(screen, (255, 255, 255), (int(sector_x), int(sector_y)), 15, 2)
            
            # Draw label
            text_surface = self.small_font.render(label, True, (255, 255, 255))
            text_rect = text_surface.get_rect(center=(sector_x, sector_y + 25))
            
            # Draw text background for better readability
            background_rect = text_rect.inflate(6, 4)
            pygame.draw.rect(screen, (0, 0, 0, 150), background_rect)
            screen.blit(text_surface, text_rect)
        
        # Draw the main transparent menu surface
        screen.blit(menu_surface, menu_rect)
        
        # Draw center dot
        pygame.draw.circle(screen, (255, 255, 255), self.center_pos, 3)
        
        # Draw instruction text
        instruction = "Select ping type"
        instruction_surface = self.font.render(instruction, True, (255, 255, 255))
        instruction_rect = instruction_surface.get_rect(center=(center_x, center_y - self.radius - 30))
        
        # Background for instruction text
        bg_rect = instruction_rect.inflate(10, 6)
        pygame.draw.rect(screen, (0, 0, 0, 180), bg_rect)
        screen.blit(instruction_surface, instruction_rect)
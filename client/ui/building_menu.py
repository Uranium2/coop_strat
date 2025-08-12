import pygame
from typing import Dict, List, Optional, Tuple

from shared.constants.game_constants import BUILDING_TYPES, COLORS
from shared.models.game_models import BuildingType, Resources


class BuildingMenu:
    def __init__(self, screen_width: int, screen_height: int):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.visible = False
        self.selected_building_type: Optional[BuildingType] = None
        self.player_resources: Optional[Resources] = None
        
        # UI layout
        self.menu_width = 400
        self.menu_height = 300
        self.menu_x = screen_width - self.menu_width - 20
        self.menu_y = screen_height - self.menu_height - 20
        
        # Building buttons layout
        self.button_width = 120
        self.button_height = 80
        self.button_margin = 10
        self.buttons_per_row = 3
        
        # Calculate building button positions
        self.building_buttons = {}
        self._setup_building_buttons()
        
        # Fonts
        self.font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 18)

    def _setup_building_buttons(self):
        """Setup building button positions and categories"""
        # Group buildings by category for better UI organization
        building_categories = {
            "Resource": ["FARM", "MINE", "WOOD_CUTTER", "GOLD_MINE"],
            "Defensive": ["TOWER", "CANNON_FOUNDRY"],
            "Upgrade": ["BARRACKS", "ARCHERY_RANGE"],
            "Special": ["WALL"]
        }
        
        button_index = 0
        for category, building_types in building_categories.items():
            for building_type in building_types:
                if building_type in [bt.value for bt in BuildingType]:
                    row = button_index // self.buttons_per_row
                    col = button_index % self.buttons_per_row
                    
                    x = self.menu_x + 20 + col * (self.button_width + self.button_margin)
                    y = self.menu_y + 50 + row * (self.button_height + self.button_margin)
                    
                    self.building_buttons[building_type] = {
                        "rect": pygame.Rect(x, y, self.button_width, self.button_height),
                        "category": category
                    }
                    button_index += 1

    def show(self, player_resources: Resources):
        """Show the building menu with current player resources"""
        self.visible = True
        self.player_resources = player_resources

    def hide(self):
        """Hide the building menu"""
        self.visible = False
        self.selected_building_type = None

    def handle_event(self, event: pygame.event.Event) -> Optional[BuildingType]:
        """Handle mouse events and return selected building type"""
        if not self.visible:
            return None
            
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                mouse_pos = event.pos  # Use event position instead of pygame.mouse.get_pos()
                
                # Check building button clicks
                for building_type, button_info in self.building_buttons.items():
                    if button_info["rect"].collidepoint(mouse_pos):
                        if self._can_afford_building(building_type):
                            self.selected_building_type = BuildingType(building_type)
                            return self.selected_building_type
                
                # Don't auto-hide when clicking outside - let the game scene handle this
                # The game scene will hide the menu when appropriate (like when selecting non-heroes)
        
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.hide()
        
        return None

    def _can_afford_building(self, building_type: str) -> bool:
        """Check if player can afford the building"""
        if not self.player_resources:
            return False
            
        building_info = BUILDING_TYPES.get(building_type)
        if not building_info:
            return False
            
        cost = building_info.get("cost", {})
        for resource, amount in cost.items():
            if getattr(self.player_resources, resource, 0) < amount:
                return False
        
        return True

    def render(self, screen: pygame.Surface):
        """Render the building menu"""
        if not self.visible:
            return
            
        # Draw menu background
        menu_rect = pygame.Rect(self.menu_x, self.menu_y, self.menu_width, self.menu_height)
        pygame.draw.rect(screen, COLORS["DARK_GRAY"], menu_rect)
        pygame.draw.rect(screen, COLORS["WHITE"], menu_rect, 2)
        
        # Draw title
        title_text = self.font.render("Build Menu", True, COLORS["WHITE"])
        screen.blit(title_text, (self.menu_x + 20, self.menu_y + 10))
        
        # Draw building buttons
        for building_type, button_info in self.building_buttons.items():
            self._render_building_button(screen, building_type, button_info)
        
        # Draw close instruction
        close_text = self.small_font.render("Press ESC or click outside to close", True, COLORS["GRAY"])
        screen.blit(close_text, (self.menu_x + 20, self.menu_y + self.menu_height - 30))

    def _render_building_button(self, screen: pygame.Surface, building_type: str, button_info: Dict):
        """Render a single building button"""
        rect = button_info["rect"]
        can_afford = self._can_afford_building(building_type)
        
        # Button background color
        if can_afford:
            if self.selected_building_type and self.selected_building_type.value == building_type:
                color = COLORS["GREEN"]
            else:
                color = COLORS["BLUE"]
        else:
            color = COLORS["GRAY"]
        
        pygame.draw.rect(screen, color, rect)
        pygame.draw.rect(screen, COLORS["WHITE"], rect, 1)
        
        # Building name
        name_parts = building_type.replace("_", " ").split()
        if len(name_parts) > 1:
            line1 = name_parts[0]
            line2 = " ".join(name_parts[1:])
            name_text1 = self.small_font.render(line1, True, COLORS["WHITE"])
            name_text2 = self.small_font.render(line2, True, COLORS["WHITE"])
            screen.blit(name_text1, (rect.x + 5, rect.y + 5))
            screen.blit(name_text2, (rect.x + 5, rect.y + 20))
        else:
            name_text = self.small_font.render(building_type, True, COLORS["WHITE"])
            screen.blit(name_text, (rect.x + 5, rect.y + 5))
        
        # Cost information
        building_info = BUILDING_TYPES.get(building_type, {})
        cost = building_info.get("cost", {})
        
        y_offset = 40
        for resource, amount in cost.items():
            if self.player_resources:
                current = getattr(self.player_resources, resource, 0)
                cost_color = COLORS["GREEN"] if current >= amount else COLORS["RED"]
            else:
                cost_color = COLORS["WHITE"]
                
            cost_text = self.small_font.render(f"{resource}: {amount}", True, cost_color)
            screen.blit(cost_text, (rect.x + 5, rect.y + y_offset))
            y_offset += 12

    def get_selected_building_type(self) -> Optional[BuildingType]:
        """Get the currently selected building type"""
        return self.selected_building_type

    def clear_selection(self):
        """Clear the current building selection"""
        self.selected_building_type = None
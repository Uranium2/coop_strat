import pygame
from typing import Optional, Tuple

from shared.constants.game_constants import BUILDING_TYPES, COLORS, TILE_SIZE
from shared.models.game_models import BuildingType, Position


class BuildingPlacer:
    def __init__(self):
        self.building_type: Optional[BuildingType] = None
        self.preview_position: Optional[Position] = None
        self.is_valid_placement = False
        
    def start_placement(self, building_type: BuildingType):
        """Start placing a building"""
        self.building_type = building_type
        self.preview_position = None
        self.is_valid_placement = False
        
    def stop_placement(self):
        """Stop placing a building"""
        self.building_type = None
        self.preview_position = None
        self.is_valid_placement = False
        
    def update_position(self, world_pos: Position, game_state, player_id: str):
        """Update the preview position and check validity"""
        if not self.building_type:
            return
            
        # Snap to grid
        grid_x = int(world_pos.x // TILE_SIZE) * TILE_SIZE
        grid_y = int(world_pos.y // TILE_SIZE) * TILE_SIZE
        self.preview_position = Position(x=grid_x, y=grid_y)
        
        # Check if placement is valid
        self.is_valid_placement = self._check_placement_validity(
            self.preview_position, game_state, player_id
        )
        
    def _check_placement_validity(self, position: Position, game_state, player_id: str) -> bool:
        """Check if the building can be placed at the given position"""
        if not self.building_type or not position:
            return False
            
        building_info = BUILDING_TYPES.get(self.building_type.value)
        if not building_info:
            return False
            
        size = building_info["size"]
        
        # Check bounds
        if (position.x < 0 or position.y < 0 or 
            position.x + size[0] * TILE_SIZE > len(game_state.map_data[0]) * TILE_SIZE or
            position.y + size[1] * TILE_SIZE > len(game_state.map_data) * TILE_SIZE):
            return False
            
        # Check fog of war - all tiles must be explored
        building_start_x = int(position.x // TILE_SIZE)
        building_start_y = int(position.y // TILE_SIZE)
        building_end_x = building_start_x + size[0]
        building_end_y = building_start_y + size[1]
        
        if hasattr(game_state, 'fog_of_war') and game_state.fog_of_war:
            for tile_y in range(building_start_y, building_end_y):
                for tile_x in range(building_start_x, building_end_x):
                    if (tile_y >= len(game_state.fog_of_war) or 
                        tile_x >= len(game_state.fog_of_war[0]) or
                        not game_state.fog_of_war[tile_y][tile_x]):
                        return False  # Cannot build in unexplored areas
            
        # Check for overlapping buildings
        for building in game_state.buildings.values():
            if self._buildings_overlap(position, size, building.position, building.size):
                return False
                
        # Check for overlapping heroes (except builder)
        for hero in game_state.heroes.values():
            if hero.player_id != player_id:  # Allow builder to place on their own position
                hero_tile_x = int(hero.position.x // TILE_SIZE)
                hero_tile_y = int(hero.position.y // TILE_SIZE)
                
                if (building_start_x <= hero_tile_x < building_end_x and
                    building_start_y <= hero_tile_y < building_end_y):
                    return False
                    
        # Check for overlapping units
        for unit in game_state.units.values():
            unit_tile_x = int(unit.position.x // TILE_SIZE)
            unit_tile_y = int(unit.position.y // TILE_SIZE)
            
            if (building_start_x <= unit_tile_x < building_end_x and
                building_start_y <= unit_tile_y < building_end_y):
                return False
                
        return True
        
    def _buildings_overlap(self, pos1: Position, size1: Tuple[int, int], 
                          pos2: Position, size2: Tuple[int, int]) -> bool:
        """Check if two buildings overlap"""
        # Convert positions to tile coordinates
        x1, y1 = int(pos1.x // TILE_SIZE), int(pos1.y // TILE_SIZE)
        x2, y2 = int(pos2.x // TILE_SIZE), int(pos2.y // TILE_SIZE)
        
        # Check overlap using proper rectangle collision detection
        # Building 1: from (x1, y1) to (x1 + size1[0], y1 + size1[1])
        # Building 2: from (x2, y2) to (x2 + size2[0], y2 + size2[1])
        return not (x1 + size1[0] <= x2 or x2 + size2[0] <= x1 or
                   y1 + size1[1] <= y2 or y2 + size2[1] <= y1)
        
    def get_placement_info(self) -> Optional[Tuple[BuildingType, Position, bool]]:
        """Get current placement info"""
        if self.building_type and self.preview_position:
            return (self.building_type, self.preview_position, self.is_valid_placement)
        return None
        
    def render_preview(self, screen: pygame.Surface, camera_offset: Tuple[int, int]):
        """Render the building placement preview"""
        if not self.building_type or not self.preview_position:
            return
            
        building_info = BUILDING_TYPES.get(self.building_type.value)
        if not building_info:
            return
            
        size = building_info["size"]
        
        # Calculate screen position
        screen_x = self.preview_position.x - camera_offset[0]
        screen_y = self.preview_position.y - camera_offset[1]
        
        # Building preview rectangle
        preview_rect = pygame.Rect(
            screen_x, screen_y,
            size[0] * TILE_SIZE, size[1] * TILE_SIZE
        )
        
        # Choose color based on validity
        if self.is_valid_placement:
            color = (*COLORS["GREEN"][:3], 128)  # Semi-transparent green
            border_color = COLORS["GREEN"]
        else:
            color = (*COLORS["RED"][:3], 128)  # Semi-transparent red
            border_color = COLORS["RED"]
            
        # Draw preview (need to create a surface for alpha blending)
        preview_surface = pygame.Surface((size[0] * TILE_SIZE, size[1] * TILE_SIZE), pygame.SRCALPHA)
        preview_surface.fill(color)
        screen.blit(preview_surface, (screen_x, screen_y))
        
        # Draw border
        pygame.draw.rect(screen, border_color, preview_rect, 2)
        
        # Draw building name
        font = pygame.font.Font(None, 24)
        name_text = font.render(self.building_type.value.replace("_", " "), True, COLORS["WHITE"])
        text_rect = name_text.get_rect()
        text_rect.center = (int(screen_x + preview_rect.width // 2), int(screen_y - 20))
        screen.blit(name_text, text_rect)
        
        # Draw cost if invalid
        if not self.is_valid_placement:
            small_font = pygame.font.Font(None, 18)
            invalid_text = small_font.render("Invalid Placement", True, COLORS["RED"])
            invalid_rect = invalid_text.get_rect()
            invalid_rect.center = (int(screen_x + preview_rect.width // 2), int(screen_y + preview_rect.height + 10))
            screen.blit(invalid_text, invalid_rect)
            
    def is_placing(self) -> bool:
        """Check if currently placing a building"""
        return self.building_type is not None
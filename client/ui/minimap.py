import pygame
from shared.constants.game_constants import COLORS, MAP_WIDTH, MAP_HEIGHT
from shared.models.game_models import GameState, TileType

class Minimap:
    def __init__(self, x: int, y: int, width: int, height: int):
        self.rect = pygame.Rect(x, y, width, height)
        self.scale_x = width / MAP_WIDTH
        self.scale_y = height / MAP_HEIGHT
    
    def handle_click(self, mouse_pos: tuple, button: int) -> tuple:
        """Handle mouse clicks on the minimap. Returns (world_x, world_y) if clicked, None otherwise"""
        if not self.rect.collidepoint(mouse_pos):
            return None
        
        # Convert minimap click to world coordinates
        local_x = mouse_pos[0] - self.rect.x
        local_y = mouse_pos[1] - self.rect.y
        
        world_x = local_x / self.scale_x
        world_y = local_y / self.scale_y
        
        # Ensure coordinates are within map bounds
        world_x = max(0, min(MAP_WIDTH - 1, world_x))
        world_y = max(0, min(MAP_HEIGHT - 1, world_y))
        
        return (world_x, world_y, button)
        
    def render(self, screen: pygame.Surface, game_state: GameState, player_id: str, camera_x: float = 0, camera_y: float = 0, screen_width: int = 1920, screen_height: int = 1080):
        pygame.draw.rect(screen, COLORS["BLACK"], self.rect)
        pygame.draw.rect(screen, COLORS["WHITE"], self.rect, 2)
        
        # Render map tiles (resources) only for explored areas
        self._render_map_tiles(screen, game_state)
        # Render fog of war over unexplored areas
        self._render_fog_of_war(screen, game_state, player_id)
        # Render buildings and units on top
        self._render_buildings(screen, game_state)
        self._render_heroes(screen, game_state, player_id)
        self._render_enemies(screen, game_state)
        self._render_pings(screen, game_state)
        # Render viewport rectangle on top
        self._render_viewport_rectangle(screen, camera_x, camera_y, screen_width, screen_height)
    
    def _render_map_tiles(self, screen: pygame.Surface, game_state: GameState):
        # Check if fog of war data exists
        shared_fog = game_state.fog_of_war
        
        # Render at 1:1 resolution - each game tile maps to 1 minimap pixel
        for y in range(MAP_HEIGHT):
            for x in range(MAP_WIDTH):
                # Bounds check for map data
                if y >= len(game_state.map_data) or x >= len(game_state.map_data[y]):
                    continue
                
                # Check if this tile is explored
                is_explored = False  # Default to hidden if no fog data
                if shared_fog and y < len(shared_fog) and x < len(shared_fog[y]):
                    is_explored = shared_fog[y][x]
                
                if not is_explored:
                    continue  # Skip unexplored tiles
                
                # Check if this tile has a resource
                tile_type = game_state.map_data[y][x]
                if tile_type not in [TileType.WOOD, TileType.STONE, TileType.WHEAT, TileType.METAL, TileType.GOLD]:
                    continue
                
                # Get color for resource type
                if tile_type == TileType.WOOD:
                    color = (0, 100, 0)
                elif tile_type == TileType.STONE:
                    color = (128, 128, 128)
                elif tile_type == TileType.WHEAT:
                    color = (200, 200, 0)
                elif tile_type == TileType.METAL:
                    color = (150, 150, 150)
                elif tile_type == TileType.GOLD:
                    color = (255, 215, 0)
                else:
                    continue
                
                # Calculate minimap pixel position
                mini_x = self.rect.x + int(x * self.scale_x)
                mini_y = self.rect.y + int(y * self.scale_y)
                
                # Draw single pixel for each tile
                mini_rect = pygame.Rect(mini_x, mini_y, max(1, int(self.scale_x)), max(1, int(self.scale_y)))
                pygame.draw.rect(screen, color, mini_rect)
    
    def _render_fog_of_war(self, screen: pygame.Surface, game_state: GameState, player_id: str):
        # Use shared fog of war instead of per-player
        shared_fog = game_state.fog_of_war
        if not shared_fog:
            return
        
        # Render fog at 1:1 resolution - each game tile maps to 1 minimap pixel
        for y in range(len(shared_fog)):
            for x in range(len(shared_fog[y]) if y < len(shared_fog) else 0):
                if not shared_fog[y][x]:  # not explored
                    mini_x = self.rect.x + int(x * self.scale_x)
                    mini_y = self.rect.y + int(y * self.scale_y)
                    fog_rect = pygame.Rect(mini_x, mini_y, max(1, int(self.scale_x)), max(1, int(self.scale_y)))
                    pygame.draw.rect(screen, (50, 50, 50), fog_rect)  # Dark gray for unexplored areas
    
    def _render_buildings(self, screen: pygame.Surface, game_state: GameState):
        for building in game_state.buildings.values():
            mini_x = self.rect.x + int(building.position.x * self.scale_x)
            mini_y = self.rect.y + int(building.position.y * self.scale_y)
            
            color = COLORS["BROWN"] if building.building_type.value == "TOWN_HALL" else COLORS["GRAY"]
            pygame.draw.rect(screen, color, (mini_x, mini_y, max(2, int(building.size[0] * self.scale_x)), max(2, int(building.size[1] * self.scale_y))))
    
    def _render_heroes(self, screen: pygame.Surface, game_state: GameState, player_id: str):
        for hero in game_state.heroes.values():
            mini_x = self.rect.x + int(hero.position.x * self.scale_x)
            mini_y = self.rect.y + int(hero.position.y * self.scale_y)
            
            color = COLORS["GREEN"] if hero.player_id == player_id else COLORS["BLUE"]
            pygame.draw.circle(screen, color, (mini_x, mini_y), 2)
    
    def _render_enemies(self, screen: pygame.Surface, game_state: GameState):
        for enemy in game_state.enemies.values():
            mini_x = self.rect.x + int(enemy.position.x * self.scale_x)
            mini_y = self.rect.y + int(enemy.position.y * self.scale_y)
            
            pygame.draw.circle(screen, COLORS["RED"], (mini_x, mini_y), 1)
    
    def _render_pings(self, screen: pygame.Surface, game_state: GameState):
        """Render pings on the minimap"""
        import time
        current_time = time.time()
        
        for ping in game_state.pings.values():
            # Check if ping is still active
            age = current_time - ping.timestamp
            if age >= ping.duration:
                continue
            
            mini_x = self.rect.x + int(ping.position.x * self.scale_x)
            mini_y = self.rect.y + int(ping.position.y * self.scale_y)
            
            # Calculate fade effect
            fade_factor = 1.0 - (age / ping.duration)
            
            # Get ping color based on type
            from shared.models.game_models import PingType
            if ping.ping_type == PingType.DANGER:
                color = (255, 0, 0)  # Red
            elif ping.ping_type == PingType.HELP:
                color = (255, 255, 0)  # Yellow
            elif ping.ping_type == PingType.MOVE_HERE:
                color = (0, 255, 0)  # Green
            else:  # ATTENTION
                color = (0, 150, 255)  # Blue
            
            # Draw ping as a small circle
            radius = max(1, int(3 * fade_factor))
            pygame.draw.circle(screen, color, (mini_x, mini_y), radius)
            pygame.draw.circle(screen, COLORS["WHITE"], (mini_x, mini_y), radius, 1)
    
    def _render_viewport_rectangle(self, screen: pygame.Surface, camera_x: float, camera_y: float, screen_width: int, screen_height: int):
        """Render a red rectangle showing the current viewport area"""
        # Calculate viewport bounds in world coordinates
        from shared.constants.game_constants import TILE_SIZE, MAP_WIDTH, MAP_HEIGHT
        
        # Convert camera position to tile coordinates
        viewport_left = camera_x / TILE_SIZE
        viewport_top = camera_y / TILE_SIZE
        viewport_right = (camera_x + screen_width) / TILE_SIZE
        viewport_bottom = (camera_y + screen_height) / TILE_SIZE
        
        # Convert to minimap coordinates
        mini_left = self.rect.x + int(viewport_left * self.scale_x)
        mini_top = self.rect.y + int(viewport_top * self.scale_y)
        mini_right = self.rect.x + int(viewport_right * self.scale_x)
        mini_bottom = self.rect.y + int(viewport_bottom * self.scale_y)
        
        # Ensure rectangle stays within minimap bounds
        mini_left = max(self.rect.x, min(self.rect.x + self.rect.width, mini_left))
        mini_top = max(self.rect.y, min(self.rect.y + self.rect.height, mini_top))
        mini_right = max(self.rect.x, min(self.rect.x + self.rect.width, mini_right))
        mini_bottom = max(self.rect.y, min(self.rect.y + self.rect.height, mini_bottom))
        
        # Draw the viewport rectangle
        viewport_width = mini_right - mini_left
        viewport_height = mini_bottom - mini_top
        
        if viewport_width > 0 and viewport_height > 0:
            viewport_rect = pygame.Rect(mini_left, mini_top, viewport_width, viewport_height)
            pygame.draw.rect(screen, COLORS["RED"], viewport_rect, 2)  # 2-pixel thick red border
#!/usr/bin/env python3

import sys
import os
import json
import pygame
from typing import List, Optional, Tuple
from datetime import datetime

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from shared.models.game_models import TileType
from shared.constants.game_constants import TILE_SIZE, COLORS, MAP_WIDTH, MAP_HEIGHT

class MapEditor:
    def __init__(self, width: int = 200, height: int = 200):
        pygame.init()
        
        # Map dimensions (smaller default for easier editing)
        self.map_width = width
        self.map_height = height
        
        # Screen setup
        self.screen_width = 1400
        self.screen_height = 900
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Co-op Strategy RTS - Map Editor")
        
        # Map data - initialize with EMPTY tiles
        self.map_data: List[List[TileType]] = []
        for y in range(self.map_height):
            row = []
            for x in range(self.map_width):
                row.append(TileType.EMPTY)
            self.map_data.append(row)
        
        # Place town hall in the center (3x3 like in the game)
        center_x = self.map_width // 2
        center_y = self.map_height // 2
        # Place 3x3 town hall centered at map center
        for dy in range(-1, 2):  # -1, 0, 1
            for dx in range(-1, 2):  # -1, 0, 1
                tx, ty = center_x + dx, center_y + dy
                if 0 <= tx < self.map_width and 0 <= ty < self.map_height:
                    self.map_data[ty][tx] = TileType.TOWN_HALL
        
        # Camera/viewport - start at town hall center
        town_hall_pixel_x = center_x * TILE_SIZE
        town_hall_pixel_y = center_y * TILE_SIZE
        # Center camera on town hall
        self.camera_x = max(0, town_hall_pixel_x - (self.screen_width - 220) // 2)
        self.camera_y = max(0, town_hall_pixel_y - self.screen_height // 2)
        self.camera_speed = 5
        
        # Current selected tile type
        self.selected_tile_type = TileType.EMPTY
        
        # Available tile types and their colors
        self.tile_types = [
            TileType.EMPTY,
            TileType.WOOD,
            TileType.STONE,
            TileType.WHEAT,
            TileType.METAL,
            TileType.GOLD,
        ]
        
        self.tile_colors = {
            TileType.EMPTY: COLORS["BLACK"],
            TileType.WOOD: COLORS["DARK_GREEN"],
            TileType.STONE: COLORS["GRAY"],
            TileType.WHEAT: COLORS["YELLOW"],
            TileType.METAL: (169, 169, 169),  # Silver
            TileType.GOLD: (255, 215, 0),     # Gold
            TileType.WALL: (139, 69, 19),     # Saddle brown
            TileType.TOWN_HALL: (128, 0, 128), # Purple
        }
        
        # UI elements
        self.palette_x = self.screen_width - 200
        self.palette_y = 20
        self.palette_tile_size = 40
        
        # Fonts
        self.font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 18)
        
        # Grid display
        self.show_grid = True
        
        # Mouse state for dragging
        self.mouse_dragging = False
        self.last_drawn_tile = None
        
        self.clock = pygame.time.Clock()
        self.running = True
        
    def handle_events(self):
        """Handle pygame events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_s and pygame.key.get_pressed()[pygame.K_LCTRL]:
                    self.save_map()
                elif event.key == pygame.K_o and pygame.key.get_pressed()[pygame.K_LCTRL]:
                    self.load_map()
                elif event.key == pygame.K_n and pygame.key.get_pressed()[pygame.K_LCTRL]:
                    self.new_map()
                elif event.key == pygame.K_g:
                    self.show_grid = not self.show_grid
                elif event.key == pygame.K_1:
                    self.selected_tile_type = TileType.EMPTY
                elif event.key == pygame.K_2:
                    self.selected_tile_type = TileType.WOOD
                elif event.key == pygame.K_3:
                    self.selected_tile_type = TileType.STONE
                elif event.key == pygame.K_4:
                    self.selected_tile_type = TileType.WHEAT
                elif event.key == pygame.K_5:
                    self.selected_tile_type = TileType.METAL
                elif event.key == pygame.K_6:
                    self.selected_tile_type = TileType.GOLD
                    
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    self.mouse_dragging = True
                    self.handle_left_click(event.pos)
                elif event.button == 3:  # Right click - clear tile
                    self.mouse_dragging = True
                    self.handle_right_click(event.pos)
                    
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1 or event.button == 3:  # Left or right button released
                    self.mouse_dragging = False
                    self.last_drawn_tile = None
                    
            elif event.type == pygame.MOUSEMOTION:
                if self.mouse_dragging:
                    mouse_buttons = pygame.mouse.get_pressed()
                    if mouse_buttons[0]:  # Left mouse button held
                        self.handle_left_click(event.pos)
                    elif mouse_buttons[2]:  # Right mouse button held
                        self.handle_right_click(event.pos)
                    
        # Handle continuous key presses for camera movement
        keys = pygame.key.get_pressed()
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            self.camera_y = max(0, self.camera_y - self.camera_speed)
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            max_y = (self.map_height * TILE_SIZE) - self.screen_height + 100
            self.camera_y = min(max_y, self.camera_y + self.camera_speed)
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            self.camera_x = max(0, self.camera_x - self.camera_speed)
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            max_x = (self.map_width * TILE_SIZE) - (self.screen_width - 220)
            self.camera_x = min(max_x, self.camera_x + self.camera_speed)
            
    def is_town_hall_tile(self, tile_x: int, tile_y: int) -> bool:
        """Check if the given tile coordinates are part of the town hall area"""
        center_x = self.map_width // 2
        center_y = self.map_height // 2
        
        # Check if tile is within the 3x3 town hall area
        return (center_x - 1 <= tile_x <= center_x + 1 and 
                center_y - 1 <= tile_y <= center_y + 1)
            
    def handle_left_click(self, pos: Tuple[int, int]):
        """Handle left mouse click"""
        mouse_x, mouse_y = pos
        
        # Check if click is on palette
        if mouse_x >= self.palette_x:
            self.handle_palette_click(pos)
            return
            
        # Convert screen coordinates to world coordinates
        world_x = mouse_x + self.camera_x
        world_y = mouse_y + self.camera_y
        
        # Convert to tile coordinates
        tile_x = world_x // TILE_SIZE
        tile_y = world_y // TILE_SIZE
        
        # Place tile if within bounds, different from last drawn tile, and not on town hall
        if (0 <= tile_x < self.map_width and 0 <= tile_y < self.map_height and 
            self.last_drawn_tile != (tile_x, tile_y) and 
            not self.is_town_hall_tile(tile_x, tile_y)):
            self.map_data[tile_y][tile_x] = self.selected_tile_type
            self.last_drawn_tile = (tile_x, tile_y)
            
    def handle_right_click(self, pos: Tuple[int, int]):
        """Handle right mouse click - clear tile"""
        mouse_x, mouse_y = pos
        
        # Skip if click is on palette
        if mouse_x >= self.palette_x:
            return
            
        # Convert screen coordinates to world coordinates
        world_x = mouse_x + self.camera_x
        world_y = mouse_y + self.camera_y
        
        # Convert to tile coordinates
        tile_x = world_x // TILE_SIZE
        tile_y = world_y // TILE_SIZE
        
        # Clear tile if within bounds, different from last drawn tile, and not on town hall
        if (0 <= tile_x < self.map_width and 0 <= tile_y < self.map_height and 
            self.last_drawn_tile != (tile_x, tile_y) and 
            not self.is_town_hall_tile(tile_x, tile_y)):
            self.map_data[tile_y][tile_x] = TileType.EMPTY
            self.last_drawn_tile = (tile_x, tile_y)
            
    def handle_palette_click(self, pos: Tuple[int, int]):
        """Handle click on tile palette"""
        mouse_x, mouse_y = pos
        
        # Calculate which tile type was clicked
        palette_tile_y = (mouse_y - self.palette_y) // (self.palette_tile_size + 5)
        
        if 0 <= palette_tile_y < len(self.tile_types):
            self.selected_tile_type = self.tile_types[palette_tile_y]
            
    def render(self):
        """Render the map editor"""
        self.screen.fill(COLORS["BLACK"])
        
        # Render map tiles
        self.render_map()
        
        # Render grid
        if self.show_grid:
            self.render_grid()
        
        # Render UI
        self.render_palette()
        self.render_info()
        
        pygame.display.flip()
        
    def render_map(self):
        """Render the map tiles"""
        # Calculate visible tile range
        start_x = max(0, self.camera_x // TILE_SIZE)
        start_y = max(0, self.camera_y // TILE_SIZE)
        end_x = min(self.map_width, (self.camera_x + self.screen_width - 220) // TILE_SIZE + 1)
        end_y = min(self.map_height, (self.camera_y + self.screen_height) // TILE_SIZE + 1)
        
        # Render visible tiles
        for y in range(start_y, end_y):
            for x in range(start_x, end_x):
                tile_type = self.map_data[y][x]
                color = self.tile_colors.get(tile_type, COLORS["PURPLE"])
                
                # Calculate screen position
                screen_x = (x * TILE_SIZE) - self.camera_x
                screen_y = (y * TILE_SIZE) - self.camera_y
                
                # Render tile
                pygame.draw.rect(
                    self.screen,
                    color,
                    (screen_x, screen_y, TILE_SIZE, TILE_SIZE)
                )
                
    def render_grid(self):
        """Render grid lines"""
        # Calculate visible tile range
        start_x = max(0, self.camera_x // TILE_SIZE)
        start_y = max(0, self.camera_y // TILE_SIZE)
        end_x = min(self.map_width, (self.camera_x + self.screen_width - 220) // TILE_SIZE + 2)
        end_y = min(self.map_height, (self.camera_y + self.screen_height) // TILE_SIZE + 2)
        
        # Vertical lines
        for x in range(start_x, end_x):
            screen_x = (x * TILE_SIZE) - self.camera_x
            if 0 <= screen_x <= self.screen_width - 220:
                pygame.draw.line(
                    self.screen,
                    COLORS["DARK_GRAY"],
                    (screen_x, 0),
                    (screen_x, self.screen_height),
                    1
                )
        
        # Horizontal lines  
        for y in range(start_y, end_y):
            screen_y = (y * TILE_SIZE) - self.camera_y
            if 0 <= screen_y <= self.screen_height:
                pygame.draw.line(
                    self.screen,
                    COLORS["DARK_GRAY"],
                    (0, screen_y),
                    (self.screen_width - 220, screen_y),
                    1
                )
                
    def render_palette(self):
        """Render the tile type palette"""
        # Background
        pygame.draw.rect(
            self.screen,
            COLORS["DARK_GRAY"],
            (self.palette_x - 10, 0, 220, self.screen_height)
        )
        
        # Title
        title = self.font.render("Tile Palette", True, COLORS["WHITE"])
        self.screen.blit(title, (self.palette_x, 5))
        
        # Tile types
        for i, tile_type in enumerate(self.tile_types):
            y = self.palette_y + i * (self.palette_tile_size + 5)
            
            # Tile preview
            color = self.tile_colors.get(tile_type, COLORS["PURPLE"])
            pygame.draw.rect(
                self.screen,
                color,
                (self.palette_x, y, self.palette_tile_size, self.palette_tile_size)
            )
            
            # Selection highlight
            if tile_type == self.selected_tile_type:
                pygame.draw.rect(
                    self.screen,
                    COLORS["WHITE"],
                    (self.palette_x - 2, y - 2, self.palette_tile_size + 4, self.palette_tile_size + 4),
                    2
                )
            
            # Label
            label = self.small_font.render(tile_type.value, True, COLORS["WHITE"])
            self.screen.blit(label, (self.palette_x + self.palette_tile_size + 5, y + 10))
            
            # Hotkey
            hotkey = str(i + 1)
            hotkey_text = self.small_font.render(f"({hotkey})", True, COLORS["GRAY"])
            self.screen.blit(hotkey_text, (self.palette_x + self.palette_tile_size + 5, y + 25))
            
    def render_info(self):
        """Render information panel"""
        info_y = self.palette_y + len(self.tile_types) * (self.palette_tile_size + 5) + 40
        
        # Controls
        controls = [
            "Controls:",
            "WASD/Arrows - Move camera",
            "Left Click/Drag - Place tiles",
            "Right Click/Drag - Clear tiles",
            "1-6 - Select tile type",
            "G - Toggle grid",
            "",
            "File Operations:",
            "Ctrl+S - Save map",
            "Ctrl+O - Load map",
            "Ctrl+N - New map",
            "",
            f"Map Size: {self.map_width}x{self.map_height}",
            f"Selected: {self.selected_tile_type.value}",
        ]
        
        for i, text in enumerate(controls):
            if text:
                color = COLORS["YELLOW"] if text.endswith(":") else COLORS["WHITE"]
                rendered = self.small_font.render(text, True, color)
                self.screen.blit(rendered, (self.palette_x, info_y + i * 18))
                
    def save_map(self):
        """Save current map to file"""
        # Create maps directory if it doesn't exist
        os.makedirs("maps", exist_ok=True)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"maps/custom_map_{timestamp}.json"
        
        # Prepare map data for saving
        map_data_str = []
        for row in self.map_data:
            row_str = []
            for tile in row:
                row_str.append(tile.value)
            map_data_str.append(row_str)
        
        # Create map file data
        map_file_data = {
            "metadata": {
                "name": f"Custom Map {timestamp}",
                "created": datetime.now().isoformat(),
                "version": "1.0",
                "width": self.map_width,
                "height": self.map_height,
                "tile_size": TILE_SIZE
            },
            "map_data": map_data_str,
            "spawn_points": [],  # Future: add spawn point editor
            "objectives": [],    # Future: add objective editor
        }
        
        try:
            with open(filename, 'w') as f:
                json.dump(map_file_data, f, indent=2)
            print(f"✅ Map saved to {filename}")
        except Exception as e:
            print(f"❌ Failed to save map: {e}")
            
    def load_map(self):
        """Load map from file"""
        # List available map files
        if not os.path.exists("maps"):
            print("📂 No maps directory found. Create some maps first!")
            return
            
        map_files = sorted([f for f in os.listdir("maps") if f.endswith('.json')])
        
        if not map_files:
            print("📂 No map files found in maps/ directory")
            return
            
        print("\n📂 Available maps:")
        for i, filename in enumerate(map_files):
            print(f"   {i + 1}. {filename}")
            
        print(f"   0. Cancel")
        print()
        
        # Get user input for map selection
        try:
            choice = input("🗺️ Enter map number to load (or 0 to cancel): ").strip()
            
            if choice == "0" or choice.lower() == "cancel":
                print("❌ Load cancelled")
                return
                
            choice_num = int(choice)
            
            if 1 <= choice_num <= len(map_files):
                filename = map_files[choice_num - 1]
                filepath = os.path.join("maps", filename)
            else:
                print(f"❌ Invalid choice. Please enter 1-{len(map_files)} or 0 to cancel")
                return
                
        except ValueError:
            print("❌ Invalid input. Please enter a number")
            return
        except KeyboardInterrupt:
            print("\n❌ Load cancelled")
            return
        
        try:
            with open(filepath, 'r') as f:
                map_data = json.load(f)
                
            # Validate map data
            if "map_data" not in map_data:
                print(f"❌ Invalid map file: missing map_data")
                return
                
            # Load metadata
            metadata = map_data.get("metadata", {})
            new_width = metadata.get("width", len(map_data["map_data"][0]))
            new_height = metadata.get("height", len(map_data["map_data"]))
            
            # Update map dimensions
            self.map_width = new_width
            self.map_height = new_height
            
            # Load map tiles
            self.map_data = []
            for row_data in map_data["map_data"]:
                row = []
                for tile_str in row_data:
                    # Convert string back to TileType enum
                    try:
                        tile_type = TileType(tile_str)
                        row.append(tile_type)
                    except ValueError:
                        # If tile type is unknown, default to EMPTY
                        row.append(TileType.EMPTY)
                self.map_data.append(row)
                
            print(f"✅ Loaded map: {filename}")
            print(f"   Size: {self.map_width}x{self.map_height}")
            
        except Exception as e:
            print(f"❌ Failed to load map: {e}")
            
    def load_specific_map(self, filename):
        """Load a specific map by filename"""
        if not filename.endswith('.json'):
            filename += '.json'
            
        # Check if file exists in maps directory
        if not filename.startswith('maps/'):
            filepath = os.path.join("maps", filename)
        else:
            filepath = filename
            
        if not os.path.exists(filepath):
            print(f"❌ Map file not found: {filepath}")
            return
            
        try:
            with open(filepath, 'r') as f:
                map_data = json.load(f)
                
            # Validate map data
            if "map_data" not in map_data:
                print(f"❌ Invalid map file: missing map_data")
                return
                
            # Load metadata
            metadata = map_data.get("metadata", {})
            new_width = metadata.get("width", len(map_data["map_data"][0]))
            new_height = metadata.get("height", len(map_data["map_data"]))
            
            # Update map dimensions
            self.map_width = new_width
            self.map_height = new_height
            
            # Load map tiles
            self.map_data = []
            for row_data in map_data["map_data"]:
                row = []
                for tile_str in row_data:
                    # Convert string back to TileType enum
                    try:
                        tile_type = TileType(tile_str)
                        row.append(tile_type)
                    except ValueError:
                        # If tile type is unknown, default to EMPTY
                        row.append(TileType.EMPTY)
                self.map_data.append(row)
                
            print(f"✅ Loaded map: {filename}")
            print(f"   Size: {self.map_width}x{self.map_height}")
            
        except Exception as e:
            print(f"❌ Failed to load map {filename}: {e}")
        
    def new_map(self):
        """Create a new empty map with town hall in center"""
        for y in range(self.map_height):
            for x in range(self.map_width):
                self.map_data[y][x] = TileType.EMPTY
        
        # Place town hall in the center (3x3 like in the game)
        center_x = self.map_width // 2
        center_y = self.map_height // 2
        # Place 3x3 town hall centered at map center
        for dy in range(-1, 2):  # -1, 0, 1
            for dx in range(-1, 2):  # -1, 0, 1
                tx, ty = center_x + dx, center_y + dy
                if 0 <= tx < self.map_width and 0 <= ty < self.map_height:
                    self.map_data[ty][tx] = TileType.TOWN_HALL
        
        print(f"🗺️ Created new map with 3x3 town hall centered at ({center_x}, {center_y})")
        
    def run(self):
        """Main editor loop"""
        print("🗺️ Map Editor Started!")
        print("📋 Controls:")
        print("   - WASD/Arrow keys: Move camera")
        print("   - 1-8: Select tile type (1=Empty, 2=Wood, 3=Stone, 4=Wheat, 5=Metal, 6=Gold, 7=Wall, 8=Town Hall)")
        print("   - Left click/drag: Place tiles")
        print("   - Right click/drag: Clear tiles") 
        print("   - G: Toggle grid")
        print("   - Ctrl+S: Save map")
        print("   - Ctrl+O: Load map")
        print("   - Ctrl+N: New map")
        print("   - ESC: Exit")
        
        while self.running:
            self.handle_events()
            self.render()
            self.clock.tick(60)
            
        pygame.quit()

if __name__ == "__main__":
    # Allow custom map size as command line arguments
    import argparse
    
    parser = argparse.ArgumentParser(description="Co-op Strategy RTS Map Editor")
    parser.add_argument("--width", type=int, default=80, help="Map width in tiles (default: 80)")
    parser.add_argument("--height", type=int, default=60, help="Map height in tiles (default: 60)")
    
    args = parser.parse_args()
    
    editor = MapEditor(args.width, args.height)
    editor.run()
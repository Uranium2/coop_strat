import asyncio
import math
import os
from typing import Any, Dict

import pygame

from client.scenes.menu_scene import MenuScene
from client.ui.building_menu import BuildingMenu
from client.ui.building_placer import BuildingPlacer
from client.ui.minimap import Minimap
from client.ui.radial_ping_menu import RadialPingMenu
from client.ui.resource_panel import ResourcePanel
from client.ui.selection_panel import SelectionPanel
from client.utils.network_manager import NetworkManager
from shared.constants.game_constants import (
    COLORS,
    FOG_COLOR,
    MAP_HEIGHT,
    MAP_WIDTH,
    TILE_SIZE,
)
from shared.models.game_models import (
    GameOverReason,
    GameState,
    Position,
    TileType,
)


class GameScene:
    def __init__(
        self,
        screen: pygame.Surface,
        network_manager: NetworkManager,
        initial_game_state: Dict[str, Any],
    ):
        self.screen = screen
        self.network_manager = network_manager

        try:
            self.game_state = GameState(**initial_game_state)
            print(f"GameState created successfully: active={self.game_state.is_active}")
        except Exception as e:
            print(f"Failed to create GameState: {e}")
            print(f"Initial game state keys: {list(initial_game_state.keys())}")
            raise

        self.camera_x = 0
        self.camera_y = 0
        self.selected_entity = None
        self.next_scene = None
        self.build_mode = None

        # Track pressed keys for smooth camera movement
        self.keys_pressed = {
            pygame.K_UP: False,
            pygame.K_DOWN: False,
            pygame.K_LEFT: False,
            pygame.K_RIGHT: False,
        }

        # Center camera on hero immediately at initialization
        self._center_camera_on_hero()

        self.build_keys = {
            pygame.K_w: "WALL",
            pygame.K_t: "TOWER",
            pygame.K_f: "FARM",
            pygame.K_m: "MINE",
            pygame.K_l: "WOOD_CUTTER",
            pygame.K_g: "GOLD_MINE",
            pygame.K_b: "BARRACKS",
        }

        self.minimap = Minimap(20, screen.get_height() - 220, 200, 200)
        self.resource_panel = ResourcePanel(screen.get_width() - 300, 20, 280, 80)
        self.selection_panel = SelectionPanel(
            screen.get_width() // 2 - 150, screen.get_height() - 120, 300, 100
        )
        self.radial_ping_menu = RadialPingMenu()

        # Building UI components
        self.building_menu = BuildingMenu(screen.get_width(), screen.get_height())
        self.building_placer = BuildingPlacer()

        # Track CTRL key state for ping menu
        self.ctrl_pressed = False

        # ESC menu state
        self.esc_menu_open = False
        self.esc_menu_buttons = {
            "continue": pygame.Rect(400, 250, 200, 50),
            "quit_to_menu": pygame.Rect(400, 320, 200, 50),
        }
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)

        # Pending build state for automatic construction when hero arrives
        self.pending_build = None

        # Gathering range visualization toggle - now controls hiding all ranges
        self.hide_all_gathering_ranges = False

        # Debug visualization toggles
        self.show_grid = False
        self.show_waypoints = False

        self.fog_surface = pygame.Surface(
            (MAP_WIDTH * TILE_SIZE, MAP_HEIGHT * TILE_SIZE), pygame.SRCALPHA
        )
        self.tile_colors = {
            TileType.EMPTY: COLORS["BLACK"],
            TileType.WOOD: COLORS["DARK_GREEN"],
            TileType.STONE: COLORS["GRAY"],
            TileType.WHEAT: COLORS["YELLOW"],
            TileType.METAL: COLORS["GRAY"],
            TileType.GOLD: COLORS["YELLOW"],
        }

        # Load tile images
        self.tree_images, self.wheat_images, self.metal_images, self.gold_images = (
            self._load_tile_images()
        )

        self.network_manager.register_handler("game_update", self._on_game_update)
        self.network_manager.register_handler("hero_moved", self._on_hero_moved)
        self.network_manager.register_handler(
            "building_placed", self._on_building_placed
        )

        self._update_fog_of_war()

    def _load_tile_images(self):
        """Load and scale tree, wheat, metal, and gold images for rendering"""
        tree_images = []
        wheat_images = []
        metal_images = []
        gold_images = []
        assets_path = os.path.join("client", "assets", "tiles")

        # Load tree images (tree_0.png to tree_3.png)
        for i in range(4):
            try:
                image_path = os.path.join(assets_path, f"tree_{i}.png")
                image = pygame.image.load(image_path).convert_alpha()

                # Scale image to fit tile size while maintaining aspect ratio
                # Make image fill most of the tile width, height can extend above
                target_width = int(TILE_SIZE * 0.9)  # 90% of tile width
                aspect_ratio = image.get_height() / image.get_width()
                target_height = int(target_width * aspect_ratio)

                scaled_image = pygame.transform.scale(
                    image, (target_width, target_height)
                )
                tree_images.append(scaled_image)
            except pygame.error as e:
                print(f"Warning: Could not load tree_{i}.png: {e}")
                # Fallback to colored rectangle if image fails to load
                fallback_surface = pygame.Surface((TILE_SIZE, TILE_SIZE))
                fallback_surface.fill(COLORS["DARK_GREEN"])
                tree_images.append(fallback_surface)

        # Load wheat images (wheat_0.png to wheat_2.png)
        for i in range(3):
            try:
                image_path = os.path.join(assets_path, f"wheat_{i}.png")
                image = pygame.image.load(image_path).convert_alpha()

                # Scale image to fit tile size while maintaining aspect ratio
                target_width = int(TILE_SIZE * 0.9)  # 90% of tile width
                aspect_ratio = image.get_height() / image.get_width()
                target_height = int(target_width * aspect_ratio)

                scaled_image = pygame.transform.scale(
                    image, (target_width, target_height)
                )
                wheat_images.append(scaled_image)
            except pygame.error as e:
                print(f"Warning: Could not load wheat_{i}.png: {e}")
                # Fallback to colored rectangle if image fails to load
                fallback_surface = pygame.Surface((TILE_SIZE, TILE_SIZE))
                fallback_surface.fill(COLORS["YELLOW"])
                wheat_images.append(fallback_surface)

        # Load metal images (metal_0.png to metal_2.png)
        for i in range(1):
            try:
                image_path = os.path.join(assets_path, f"metal_{i}.png")
                image = pygame.image.load(image_path).convert_alpha()

                # Scale image to fit tile size
                scaled_image = pygame.transform.scale(image, (TILE_SIZE, TILE_SIZE))
                metal_images.append(scaled_image)
            except pygame.error as e:
                print(f"Warning: Could not load metal_{i}.png: {e}")
                # Fallback to colored rectangle if image fails to load
                fallback_surface = pygame.Surface((TILE_SIZE, TILE_SIZE))
                fallback_surface.fill(COLORS["GRAY"])
                metal_images.append(fallback_surface)

        # Load gold images (gold_0.png to gold_2.png)
        for i in range(1):
            try:
                image_path = os.path.join(assets_path, f"gold_{i}.png")
                image = pygame.image.load(image_path).convert_alpha()

                # Scale image to fit tile size
                scaled_image = pygame.transform.scale(image, (TILE_SIZE, TILE_SIZE))
                gold_images.append(scaled_image)
            except pygame.error as e:
                print(f"Warning: Could not load gold_{i}.png: {e}")
                # Fallback to colored rectangle if image fails to load
                fallback_surface = pygame.Surface((TILE_SIZE, TILE_SIZE))
                fallback_surface.fill(COLORS["YELLOW"])
                gold_images.append(fallback_surface)

        return tree_images, wheat_images, metal_images, gold_images

    def _get_tree_image_index(self, x: int, y: int) -> int:
        """Get deterministic tree image index based on tile position"""
        # Use a simple hash function to get consistent random selection
        return (x * 7 + y * 13) % len(self.tree_images)

    def _get_wheat_image_index(self, x: int, y: int) -> int:
        """Get deterministic wheat image index based on tile position"""
        # Use a different hash function to get different distribution than trees
        return (x * 11 + y * 17) % len(self.wheat_images)

    def _get_metal_image_index(self, x: int, y: int) -> int:
        """Get deterministic metal image index based on tile position"""
        # Use another hash function to get different distribution
        return (x * 19 + y * 23) % len(self.metal_images)

    def _get_gold_image_index(self, x: int, y: int) -> int:
        """Get deterministic gold image index based on tile position"""
        # Use yet another hash function to get different distribution
        return (x * 29 + y * 31) % len(self.gold_images)

    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if self.radial_ping_menu.is_active:
                    self.radial_ping_menu.deactivate()
                elif self.build_mode:
                    self.build_mode = None
                elif self.esc_menu_open:
                    self._close_esc_menu()
                else:
                    self._open_esc_menu()
            elif event.key == pygame.K_LCTRL or event.key == pygame.K_RCTRL:
                self.ctrl_pressed = True
                # Activate radial ping menu immediately at mouse position
                mouse_pos = pygame.mouse.get_pos()
                # Only activate if mouse is in the main game area (not on UI elements)
                if self._is_mouse_in_game_area(mouse_pos):
                    self.radial_ping_menu.activate(mouse_pos)
            elif (
                event.key in self.build_keys
                and self.selected_entity
                and hasattr(self.selected_entity, "hero_type")
            ):
                self.build_mode = self.build_keys[event.key]
            elif event.key == pygame.K_SPACE:
                # Toggle pause
                asyncio.create_task(
                    self.network_manager.send_game_action({"type": "toggle_pause"})
                )
            elif event.key == pygame.K_r:  # R to hide all gathering ranges
                self.hide_all_gathering_ranges = not self.hide_all_gathering_ranges
            elif event.key == pygame.K_F1:  # F1 to toggle grid overlay
                self.show_grid = not self.show_grid
            elif event.key == pygame.K_F2:  # F2 to toggle waypoint visualization
                self.show_waypoints = not self.show_waypoints
            elif event.key in self.keys_pressed:
                self.keys_pressed[event.key] = True

        elif event.type == pygame.KEYUP:
            if event.key == pygame.K_LCTRL or event.key == pygame.K_RCTRL:
                # Create ping if menu is active and something is hovered
                if self.radial_ping_menu.is_active:
                    mouse_pos = pygame.mouse.get_pos()
                    selected_ping = self.radial_ping_menu.get_selected_ping(mouse_pos)
                    if selected_ping:
                        # Create ping with selected type
                        world_pos = self._screen_to_world(
                            self.radial_ping_menu.center_pos
                        )
                        self._create_ping(world_pos[0], world_pos[1], selected_ping)
                    self.radial_ping_menu.deactivate()

                self.ctrl_pressed = False
            elif event.key in self.keys_pressed:
                self.keys_pressed[event.key] = False

        elif event.type == pygame.MOUSEMOTION:
            # Update ping menu hover if active
            if self.radial_ping_menu.is_active:
                self.radial_ping_menu.update_hover(event.pos)

        elif event.type == pygame.MOUSEBUTTONDOWN:
            # Handle ESC menu clicks first
            if self.esc_menu_open and event.button == 1:
                if self.esc_menu_buttons["continue"].collidepoint(event.pos):
                    self._close_esc_menu()
                    return
                elif self.esc_menu_buttons["quit_to_menu"].collidepoint(event.pos):
                    self._quit_to_menu()
                    return
                # If clicked outside ESC menu, close it
                elif not self._is_click_in_esc_menu(event.pos):
                    self._close_esc_menu()
                    return

            # Handle building menu events
            if self.building_menu.visible:
                selected_building = self.building_menu.handle_event(event)
                if selected_building:
                    # Start building placement mode
                    self.building_placer.start_placement(selected_building)
                    # Keep building menu open during placement preview
                    return
                # Check if click was within the building menu area to prevent further processing
                if event.button == 1:  # Only for left clicks
                    mouse_pos = event.pos
                    menu_rect = pygame.Rect(
                        self.building_menu.menu_x,
                        self.building_menu.menu_y,
                        self.building_menu.menu_width,
                        self.building_menu.menu_height,
                    )
                    if menu_rect.collidepoint(mouse_pos):
                        return  # Click was on menu, don't process further

            # Handle building placement
            if self.building_placer.is_placing() and event.button == 1:
                placement_info = self.building_placer.get_placement_info()
                if (
                    placement_info
                ):  # Valid placement position (regardless of hero proximity)
                    building_type, position, is_valid = placement_info
                    # Convert pixel coordinates to tile coordinates for server
                    from shared.constants.game_constants import TILE_SIZE

                    tile_x = int(position.x // TILE_SIZE)
                    tile_y = int(position.y // TILE_SIZE)
                    # Convert to pixel coordinates for server
                    pixel_x = tile_x * TILE_SIZE
                    pixel_y = tile_y * TILE_SIZE

                    if is_valid:  # Hero is adjacent - instant build
                        print(f"[CLIENT DEBUG] 📦 Sending instant build: {building_type.value} at pixel coords ({pixel_x}, {pixel_y})")
                        asyncio.create_task(
                            self.network_manager.send_game_action(
                                {
                                    "type": "build",
                                    "building_type": building_type.value,
                                    "position": {"x": pixel_x, "y": pixel_y},
                                }
                            )
                        )
                        self.building_placer.stop_placement()
                        # Clear building selection in menu so it returns to blue color
                        self.building_menu.clear_selection()
                    else:  # Hero is not adjacent - set up travel-to-build
                        self.pending_build = {
                            "type": "build",
                            "building_type": building_type.value,
                            "position": {"x": pixel_x, "y": pixel_y},
                        }
                        # Place fixed preview on map at click position
                        self.building_placer.place_preview_on_map(
                            position, self.game_state, self.network_manager.player_id
                        )
                        # Disable cursor preview so it doesn't follow mouse
                        self.building_placer.is_cursor_preview = False
                        # Send hero to building location
                        asyncio.create_task(
                            self.network_manager.send_game_action(
                                {
                                    "type": "move_hero",
                                    "target_position": {"x": tile_x, "y": tile_y},
                                }
                            )
                        )
                        self.building_placer.set_hero_traveling(True)
                        print(
                            f"🚶 Hero traveling to build {building_type.value} at ({tile_x}, {tile_y})"
                        )
                        print(
                            f"📍 Fixed preview placed on map at ({position.x}, {position.y})"
                        )
                    return

            # Check if ping menu is active and handle selection
            if self.radial_ping_menu.is_active and event.button == 1:
                selected_ping = self.radial_ping_menu.get_selected_ping(event.pos)
                if selected_ping:
                    # Create ping with selected type
                    world_pos = self._screen_to_world(self.radial_ping_menu.center_pos)
                    self._create_ping(world_pos[0], world_pos[1], selected_ping)
                self.radial_ping_menu.deactivate()
                return

            # Check if click is on minimap first
            minimap_click = self.minimap.handle_click(event.pos, event.button)
            if minimap_click:
                world_x, world_y, button = minimap_click
                if button == 1:  # Left click - move camera
                    self._move_camera_to_world_position(world_x, world_y)
                elif button == 3:  # Right click - create ping (default ATTENTION type)
                    self._create_ping(world_x, world_y)
            else:
                # Handle regular game area clicks
                if event.button == 1:
                    if self.build_mode:
                        self._handle_build_click(event.pos)
                    else:
                        self._handle_left_click(event.pos)
                elif event.button == 3:
                    if self.building_placer.is_placing():
                        # Right-click during building placement: cancel placement
                        self.building_placer.stop_placement()
                    elif self.build_mode:
                        self.build_mode = None
                    else:
                        self._handle_right_click(event.pos)

    def _handle_build_click(self, pos: tuple):
        world_pos = self._screen_to_world(pos)

        if (
            self.build_mode
            and self.selected_entity
            and hasattr(self.selected_entity, "hero_type")
        ):
            asyncio.create_task(
                self.network_manager.send_game_action(
                    {
                        "type": "build",
                        "building_type": self.build_mode,
                        "position": {"x": world_pos[0], "y": world_pos[1]},
                    }
                )
            )
            self.build_mode = None

    def _handle_left_click(self, pos: tuple):
        world_pos = self._screen_to_world(pos)

        hero = self._get_player_hero()
        if hero:
            distance = (
                (hero.position.x - world_pos[0]) ** 2
                + (hero.position.y - world_pos[1]) ** 2
            ) ** 0.5
            if distance <= 2:
                self.selected_entity = hero
                # Open building menu when hero is selected
                current_player = self.game_state.players.get(
                    self.network_manager.player_id
                )
                if current_player:
                    self.building_menu.show(current_player.resources)
                return

        # Check for enemy selection
        for enemy in self.game_state.enemies.values():
            distance = (
                (enemy.position.x - world_pos[0]) ** 2
                + (enemy.position.y - world_pos[1]) ** 2
            ) ** 0.5
            if distance <= 2:
                self.selected_entity = enemy
                # Hide building menu when non-hero is selected
                self.building_menu.hide()
                return

        for building in self.game_state.buildings.values():
            if (
                building.position.x
                <= world_pos[0]
                < building.position.x + building.size[0]
                and building.position.y
                <= world_pos[1]
                < building.position.y + building.size[1]
            ):
                self.selected_entity = building
                # Hide building menu when non-hero is selected
                self.building_menu.hide()
                return

        self.selected_entity = None
        # Hide building menu when nothing is selected
        self.building_menu.hide()

    def _handle_right_click(self, pos: tuple):
        world_pos = self._screen_to_world(pos)

        if self.selected_entity and hasattr(self.selected_entity, "hero_type"):
            # Check what was clicked on
            clicked_target = self._get_clicked_target(world_pos)

            if clicked_target:
                target_type, target_id = clicked_target
                # Send move to target command
                asyncio.create_task(
                    self.network_manager.send_game_action(
                        {
                            "type": "move_to_target",
                            "target_type": target_type,
                            "target_id": target_id,
                        }
                    )
                )
            else:
                # Move to position
                asyncio.create_task(
                    self.network_manager.send_game_action(
                        {
                            "type": "move_hero",
                            "target_position": {"x": world_pos[0], "y": world_pos[1]},
                        }
                    )
                )
        else:
            # No hero selected or right-clicked empty space - deselect
            self.selected_entity = None
            self.building_menu.hide()

    def _get_clicked_target(self, world_pos: tuple):
        """Determine what entity was clicked on"""
        x, y = world_pos

        # Check for heroes (prioritize over other entities)
        for hero in self.game_state.heroes.values():
            if (
                hero.player_id != self.network_manager.player_id
            ):  # Don't target own hero
                distance = (
                    (hero.position.x - x) ** 2 + (hero.position.y - y) ** 2
                ) ** 0.5
                if distance <= 1.0:  # Click tolerance
                    return ("HERO", hero.id)

        # Check for enemies
        for enemy in self.game_state.enemies.values():
            if enemy.health > 0:
                distance = (
                    (enemy.position.x - x) ** 2 + (enemy.position.y - y) ** 2
                ) ** 0.5
                if distance <= 1.0:
                    return ("ENEMY", enemy.id)

        # Check for units
        for unit in self.game_state.units.values():
            if unit.health > 0:
                distance = (
                    (unit.position.x - x) ** 2 + (unit.position.y - y) ** 2
                ) ** 0.5
                if distance <= 1.0:
                    return ("UNIT", unit.id)

        # Check for buildings
        for building in self.game_state.buildings.values():
            if building.health > 0:
                if (
                    building.position.x <= x < building.position.x + building.size[0]
                    and building.position.y
                    <= y
                    < building.position.y + building.size[1]
                ):
                    return ("BUILDING", building.id)

        return None

    def _handle_camera_movement(self, key):
        # This method is no longer used for continuous movement
        # But keep it for compatibility or one-time movements
        speed = 10
        if key == pygame.K_UP:
            self.camera_y = max(0, self.camera_y - speed)
        elif key == pygame.K_DOWN:
            self.camera_y = min(
                MAP_HEIGHT * TILE_SIZE - self.screen.get_height(), self.camera_y + speed
            )
        elif key == pygame.K_LEFT:
            self.camera_x = max(0, self.camera_x - speed)
        elif key == pygame.K_RIGHT:
            self.camera_x = min(
                MAP_WIDTH * TILE_SIZE - self.screen.get_width(), self.camera_x + speed
            )

    def _handle_continuous_camera_movement(self):
        """Handle smooth camera movement based on currently pressed keys"""
        speed = 15  # Increased from 8 for faster movement

        if self.keys_pressed[pygame.K_UP]:
            self.camera_y = max(0, self.camera_y - speed)
        if self.keys_pressed[pygame.K_DOWN]:
            self.camera_y = min(
                MAP_HEIGHT * TILE_SIZE - self.screen.get_height(), self.camera_y + speed
            )
        if self.keys_pressed[pygame.K_LEFT]:
            self.camera_x = max(0, self.camera_x - speed)
        if self.keys_pressed[pygame.K_RIGHT]:
            self.camera_x = min(
                MAP_WIDTH * TILE_SIZE - self.screen.get_width(), self.camera_x + speed
            )

    def _handle_mouse_edge_scrolling(self):
        """Handle camera movement when mouse is near screen edges"""
        mouse_x, mouse_y = pygame.mouse.get_pos()
        screen_width = self.screen.get_width()
        screen_height = self.screen.get_height()

        edge_margin = 50  # Pixels from edge to trigger scrolling
        scroll_speed = 15  # Increased from 8 for faster movement

        # Check horizontal edges
        if mouse_x < edge_margin:
            # Mouse near left edge - scroll left
            self.camera_x = max(0, self.camera_x - scroll_speed)
        elif mouse_x > screen_width - edge_margin:
            # Mouse near right edge - scroll right
            self.camera_x = min(
                MAP_WIDTH * TILE_SIZE - screen_width, self.camera_x + scroll_speed
            )

        # Check vertical edges
        if mouse_y < edge_margin:
            # Mouse near top edge - scroll up
            self.camera_y = max(0, self.camera_y - scroll_speed)
        elif mouse_y > screen_height - edge_margin:
            # Mouse near bottom edge - scroll down
            self.camera_y = min(
                MAP_HEIGHT * TILE_SIZE - screen_height, self.camera_y + scroll_speed
            )

    def _screen_to_world(self, screen_pos: tuple) -> tuple:
        world_x = (screen_pos[0] + self.camera_x) // TILE_SIZE
        world_y = (screen_pos[1] + self.camera_y) // TILE_SIZE
        return (world_x, world_y)

    def _world_to_screen(self, world_pos: tuple) -> tuple:
        screen_x = int(world_pos[0] * TILE_SIZE - self.camera_x)
        screen_y = int(world_pos[1] * TILE_SIZE - self.camera_y)
        return (screen_x, screen_y)

    def _get_player_hero(self):
        for hero in self.game_state.heroes.values():
            if hero.player_id == self.network_manager.player_id:
                return hero
        return None

    def _center_camera_on_hero(self):
        """Center the camera on the player's hero"""
        hero = self._get_player_hero()
        if hero:
            screen_center_x = self.screen.get_width() // 2
            screen_center_y = self.screen.get_height() // 2

            target_camera_x = hero.position.x * TILE_SIZE - screen_center_x
            target_camera_y = hero.position.y * TILE_SIZE - screen_center_y

            # Apply bounds checking
            self.camera_x = int(
                max(
                    0,
                    min(
                        MAP_WIDTH * TILE_SIZE - self.screen.get_width(), target_camera_x
                    ),
                )
            )
            self.camera_y = int(
                max(
                    0,
                    min(
                        MAP_HEIGHT * TILE_SIZE - self.screen.get_height(),
                        target_camera_y,
                    ),
                )
            )

    def _move_camera_to_world_position(self, world_x: float, world_y: float):
        """Move camera to center on a specific world position"""
        screen_center_x = self.screen.get_width() // 2
        screen_center_y = self.screen.get_height() // 2

        target_camera_x = world_x * TILE_SIZE - screen_center_x
        target_camera_y = world_y * TILE_SIZE - screen_center_y

        # Apply bounds checking
        self.camera_x = int(
            max(
                0, min(MAP_WIDTH * TILE_SIZE - self.screen.get_width(), target_camera_x)
            )
        )
        self.camera_y = int(
            max(
                0,
                min(MAP_HEIGHT * TILE_SIZE - self.screen.get_height(), target_camera_y),
            )
        )

    def _create_ping(self, world_x: float, world_y: float, ping_type=None):
        """Create a ping at the specified world position"""
        import time
        import uuid

        from shared.models.game_models import PingType

        # Default to ATTENTION if no type specified
        if ping_type is None:
            ping_type = PingType.ATTENTION

        ping_data = {
            "type": "create_ping",
            "ping_id": str(uuid.uuid4()),
            "position": {"x": world_x, "y": world_y},
            "ping_type": ping_type.value,
            "timestamp": time.time(),
        }

        # Send ping to server
        import asyncio

        asyncio.create_task(self.network_manager.send_message(ping_data))

    def _is_mouse_in_game_area(self, mouse_pos: tuple) -> bool:
        """Check if mouse position is in the main game area (not on UI elements)"""
        x, y = mouse_pos
        screen_width = self.screen.get_width()
        screen_height = self.screen.get_height()

        # Check if mouse is over minimap
        if 20 <= x <= 220 and screen_height - 220 <= y <= screen_height - 20:
            return False

        # Check if mouse is over resource panel (now at top right)
        if screen_width - 300 <= x <= screen_width and 20 <= y <= 100:
            return False

        # Check if mouse is over selection panel
        if (
            screen_width // 2 - 150 <= x <= screen_width // 2 + 150
            and screen_height - 120 <= y <= screen_height
        ):
            return False

        # Mouse is in game area
        return True

    def _on_game_update(self, data):
        import time

        timestamp = time.time()
        print(
            f"[DEBUG {timestamp:.3f}] Received game update data keys: {list(data.keys())}"
        )
        if "game_state" in data:
            print(
                f"[DEBUG {timestamp:.3f}] Game state keys: {list(data['game_state'].keys())}"
            )
            print(
                f"[DEBUG {timestamp:.3f}] is_active in data: {'is_active' in data['game_state']}"
            )
            print(
                f"[DEBUG {timestamp:.3f}] game_over_reason in data: {'game_over_reason' in data['game_state']}"
            )
            if "is_active" in data["game_state"]:
                is_active_value = data["game_state"]["is_active"]
                print(f"[DEBUG {timestamp:.3f}] is_active value: {is_active_value}")
                if not is_active_value:
                    print(
                        f"[DEBUG {timestamp:.3f}] *** RECEIVED is_active=False FROM SERVER ***"
                    )
            if "game_over_reason" in data["game_state"]:
                game_over_value = data["game_state"]["game_over_reason"]
                print(
                    f"[DEBUG {timestamp:.3f}] game_over_reason value: {game_over_value}"
                )
                if game_over_value != "NONE":
                    print(
                        f"[DEBUG {timestamp:.3f}] *** RECEIVED game_over_reason={game_over_value} FROM SERVER ***"
                    )

        self.game_state = GameState(**data["game_state"])
        
        # Debug: Check if buildings are received
        print(f"[DEBUG {timestamp:.3f}] Buildings received: {len(self.game_state.buildings)}")
        for building_id, building in self.game_state.buildings.items():
            print(f"[DEBUG {timestamp:.3f}] Building: {building_id} - {building.building_type.value} at ({building.position.x}, {building.position.y})")
        
        self._update_fog_of_war()

        # Check if hero reached pending build location
        if self.pending_build:
            self._check_hero_arrival_for_pending_build()

        # Check for game over conditions
        print(
            f"[DEBUG {timestamp:.3f}] After GameState creation - is_active: {self.game_state.is_active}"
        )
        print(
            f"[DEBUG {timestamp:.3f}] After GameState creation - game_over_reason: {self.game_state.game_over_reason}"
        )

        if not self.game_state.is_active:
            print(f"[DEBUG {timestamp:.3f}] *** GAME OVER DETECTED *** is_active=False")
            # Check if we have a game over reason
            game_over_reason = self.game_state.game_over_reason
            print(
                f"[DEBUG {timestamp:.3f}] Game over reason: {game_over_reason} (type: {type(game_over_reason)})"
            )
            if game_over_reason != GameOverReason.NONE:
                print(
                    f"[DEBUG {timestamp:.3f}] Creating GameOverScene with reason: {game_over_reason}"
                )
                from client.scenes.game_over_scene import GameOverScene

                self.next_scene = GameOverScene(
                    self.screen, self.network_manager, game_over_reason.value
                )
                print(
                    f"[DEBUG {timestamp:.3f}] GameOverScene created and set as next_scene"
                )
            else:
                # Fallback for generic game over
                print(
                    "[DEBUG] Game over with NONE reason - creating generic GameOverScene"
                )
                from client.scenes.game_over_scene import GameOverScene

                self.next_scene = GameOverScene(
                    self.screen, self.network_manager, "NONE"
                )
        else:
            print(
                f"[DEBUG] Game is still active (is_active={self.game_state.is_active})"
            )

    def _on_hero_moved(self, data):
        pass

    def _on_building_placed(self, data):
        pass

    def _update_fog_of_war(self):
        self.fog_surface.fill(FOG_COLOR)

        # Use shared fog of war (no longer per-player)
        shared_fog = self.game_state.fog_of_war
        if not shared_fog:
            return

        for y in range(len(shared_fog)):
            for x in range(len(shared_fog[y])):
                if shared_fog[y][x]:
                    fog_rect = pygame.Rect(
                        x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE
                    )
                    pygame.draw.rect(self.fog_surface, (0, 0, 0, 0), fog_rect)

    def update(self, dt: float):
        # Don't update camera movement when ESC menu is open
        if not self.esc_menu_open:
            # Handle continuous arrow key camera movement
            self._handle_continuous_camera_movement()

            # Handle mouse edge scrolling
            self._handle_mouse_edge_scrolling()

        # Update building placer position if placing
        if self.building_placer.is_placing():
            mouse_pos = pygame.mouse.get_pos()
            # Convert to world pixel coordinates (not tile coordinates)
            world_pixel_x = mouse_pos[0] + self.camera_x
            world_pixel_y = mouse_pos[1] + self.camera_y
            self.building_placer.update_position(
                Position(x=world_pixel_x, y=world_pixel_y),
                self.game_state,
                self.network_manager.player_id,
            )

    def render(self, screen: pygame.Surface):
        screen.fill(COLORS["BLACK"])

        self._render_map(screen)
        self._render_buildings(screen)
        # Render gathering ranges after buildings but before other entities
        if not self.hide_all_gathering_ranges:
            self._render_gathering_ranges(screen)
        self._render_enemies(screen)
        self._render_fog_of_war(screen)
        # Render heroes AFTER fog of war so they're always visible
        self._render_heroes(screen)
        # Render debug overlays
        if self.show_grid:
            self._render_grid(screen)
        if self.show_waypoints:
            self._render_waypoints(screen)
        # Render pings on top of everything else in the game world
        self._render_pings(screen)
        # Render attack effects on top of everything else
        self._render_attack_effects(screen)

        current_player = self.game_state.players.get(self.network_manager.player_id)
        if current_player:
            self.resource_panel.render(screen, current_player.resources)

        self.minimap.render(
            screen,
            self.game_state,
            self.network_manager.player_id,
            self.camera_x,
            self.camera_y,
            self.screen.get_width(),
            self.screen.get_height(),
        )

        if self.selected_entity:
            self.selection_panel.render(screen, self.selected_entity)

        if self.build_mode:
            self._render_build_info(screen)

        # Render radial ping menu on top of everything
        self.radial_ping_menu.draw(screen)

        # Render lobby ID at the top of the screen
        self._render_lobby_info(screen)

        # Render pause indicator if game is paused
        if self.game_state.is_paused:
            self._render_pause_indicator(screen)

        # Render building placement preview
        if self.building_placer.is_placing():
            self.building_placer.render_preview(screen, (self.camera_x, self.camera_y))

        # Render building menu
        self.building_menu.render(screen)

        # Render ESC menu on top of everything if open
        if self.esc_menu_open:
            self._render_esc_menu(screen)

    def _render_build_info(self, screen: pygame.Surface):
        font = pygame.font.Font(None, 24)
        text = f"Build Mode: {self.build_mode} (Right-click to cancel)"
        text_surface = font.render(text, True, COLORS["WHITE"])
        screen.blit(text_surface, (10, 10))

    def _render_lobby_info(self, screen: pygame.Surface):
        font = pygame.font.Font(None, 24)
        lobby_id = getattr(self.game_state, "lobby_id", "Unknown")

        # Get spawn timer info
        wave_number = getattr(self.game_state, "wave_number", 0)
        time_to_next_wave = getattr(self.game_state, "time_to_next_wave", 0)

        if lobby_id:
            # Display lobby ID at the top center of screen
            lobby_text = (
                f"Lobby: {lobby_id[:12]}..."
                if len(lobby_id) > 15
                else f"Lobby: {lobby_id}"
            )

            # Format spawn timer
            if time_to_next_wave > 0:
                minutes = int(time_to_next_wave // 60)
                seconds = int(time_to_next_wave % 60)
                if wave_number == 0:
                    timer_text = f"First Wave: {minutes:02d}:{seconds:02d}"
                else:
                    timer_text = f"Next Wave: {minutes:02d}:{seconds:02d}"
            else:
                if wave_number == 0:
                    timer_text = "First Wave: Starting..."
                else:
                    timer_text = "Next Wave: Starting..."

            # Render both texts
            lobby_surface = font.render(lobby_text, True, COLORS["CYAN"])
            timer_surface = font.render(timer_text, True, COLORS["YELLOW"])

            # Position lobby ID
            lobby_rect = lobby_surface.get_rect()
            lobby_rect.centerx = (
                screen.get_width() // 2 - 100
            )  # Move left to make room for timer
            lobby_rect.y = 10

            # Position timer next to lobby ID
            timer_rect = timer_surface.get_rect()
            timer_rect.centerx = screen.get_width() // 2 + 100  # Move right
            timer_rect.y = 10

            # Draw backgrounds for better visibility
            lobby_bg_rect = lobby_rect.inflate(20, 10)
            timer_bg_rect = timer_rect.inflate(20, 10)

            pygame.draw.rect(screen, (0, 0, 0, 128), lobby_bg_rect)
            pygame.draw.rect(screen, COLORS["WHITE"], lobby_bg_rect, 1)

            pygame.draw.rect(screen, (0, 0, 0, 128), timer_bg_rect)
            pygame.draw.rect(screen, COLORS["WHITE"], timer_bg_rect, 1)

            screen.blit(lobby_surface, lobby_rect)
            screen.blit(timer_surface, timer_rect)

    def _render_pause_indicator(self, screen: pygame.Surface):
        """Render the pause indicator in the top right corner"""
        font = pygame.font.Font(None, 36)
        text = "PAUSED"
        text_surface = font.render(text, True, COLORS["YELLOW"])
        text_rect = text_surface.get_rect()
        text_rect.topright = (screen.get_width() - 20, 20)

        # Draw background for better visibility
        bg_rect = text_rect.inflate(20, 10)
        pygame.draw.rect(screen, (0, 0, 0, 180), bg_rect)
        pygame.draw.rect(screen, COLORS["YELLOW"], bg_rect, 2)

        screen.blit(text_surface, text_rect)

    def _is_tile_explored(self, x: int, y: int) -> bool:
        """Check if a tile has been explored (visible through fog of war)"""
        shared_fog = self.game_state.fog_of_war
        if not shared_fog or y >= len(shared_fog) or x >= len(shared_fog[0]):
            return False
        return shared_fog[y][x]

    def _render_map(self, screen: pygame.Surface):
        start_x = max(0, int(self.camera_x) // TILE_SIZE)
        start_y = max(0, int(self.camera_y) // TILE_SIZE)
        end_x = min(
            MAP_WIDTH, (int(self.camera_x) + screen.get_width()) // TILE_SIZE + 1
        )
        end_y = min(
            MAP_HEIGHT, (int(self.camera_y) + screen.get_height()) // TILE_SIZE + 1
        )

        for y in range(start_y, end_y):
            for x in range(start_x, end_x):
                if 0 <= y < len(self.game_state.map_data) and 0 <= x < len(
                    self.game_state.map_data[y]
                ):
                    tile_type = self.game_state.map_data[y][x]

                    # Check if tile is explored - if not, show basic black terrain
                    if self._is_tile_explored(x, y):
                        # Show actual tile type with resources
                        if tile_type == TileType.WOOD:
                            # Draw the tree image directly without background
                            tree_index = self._get_tree_image_index(x, y)
                            tree_image = self.tree_images[tree_index]

                            # Position image: center horizontally, align bottom with tile bottom
                            rect = pygame.Rect(
                                x * TILE_SIZE - int(self.camera_x),
                                y * TILE_SIZE - int(self.camera_y),
                                TILE_SIZE,
                                TILE_SIZE,
                            )
                            image_x = rect.x + (TILE_SIZE - tree_image.get_width()) // 2
                            image_y = rect.y + TILE_SIZE - tree_image.get_height()

                            screen.blit(tree_image, (image_x, image_y))
                        elif tile_type == TileType.WHEAT:
                            # Draw the wheat image directly without background
                            wheat_index = self._get_wheat_image_index(x, y)
                            wheat_image = self.wheat_images[wheat_index]

                            # Position image: center horizontally, align bottom with tile bottom
                            rect = pygame.Rect(
                                x * TILE_SIZE - int(self.camera_x),
                                y * TILE_SIZE - int(self.camera_y),
                                TILE_SIZE,
                                TILE_SIZE,
                            )
                            image_x = (
                                rect.x + (TILE_SIZE - wheat_image.get_width()) // 2
                            )
                            image_y = rect.y + TILE_SIZE - wheat_image.get_height()

                            screen.blit(wheat_image, (image_x, image_y))
                        elif tile_type == TileType.METAL:
                            # Draw the metal ore image
                            metal_index = self._get_metal_image_index(x, y)
                            metal_image = self.metal_images[metal_index]

                            # Position image: center on tile
                            rect = pygame.Rect(
                                x * TILE_SIZE - int(self.camera_x),
                                y * TILE_SIZE - int(self.camera_y),
                                TILE_SIZE,
                                TILE_SIZE,
                            )

                            screen.blit(metal_image, (rect.x, rect.y))
                        elif tile_type == TileType.GOLD:
                            # Draw the gold ore image
                            gold_index = self._get_gold_image_index(x, y)
                            gold_image = self.gold_images[gold_index]

                            # Position image: center on tile
                            rect = pygame.Rect(
                                x * TILE_SIZE - int(self.camera_x),
                                y * TILE_SIZE - int(self.camera_y),
                                TILE_SIZE,
                                TILE_SIZE,
                            )

                            screen.blit(gold_image, (rect.x, rect.y))
                        else:
                            # Regular colored tile for other resource tiles
                            color = self.tile_colors.get(tile_type, COLORS["BLACK"])
                            rect = pygame.Rect(
                                x * TILE_SIZE - int(self.camera_x),
                                y * TILE_SIZE - int(self.camera_y),
                                TILE_SIZE,
                                TILE_SIZE,
                            )
                            pygame.draw.rect(screen, color, rect)
                    else:
                        # For unexplored areas, show basic black terrain (fog will cover this)
                        color = COLORS["BLACK"]
                        rect = pygame.Rect(
                            x * TILE_SIZE - int(self.camera_x),
                            y * TILE_SIZE - int(self.camera_y),
                            TILE_SIZE,
                            TILE_SIZE,
                        )
                        pygame.draw.rect(screen, color, rect)

    def _render_buildings(self, screen: pygame.Surface):
        print(f"[RENDER DEBUG] Rendering {len(self.game_state.buildings)} buildings")
        for building in self.game_state.buildings.values():
            print(f"[RENDER DEBUG] Building: {building.building_type.value} at ({building.position.x}, {building.position.y})")
            # Convert building pixel coordinates to tile coordinates for _world_to_screen
            building_tile_x = building.position.x // TILE_SIZE
            building_tile_y = building.position.y // TILE_SIZE
            screen_pos = self._world_to_screen(
                (building_tile_x, building_tile_y)
            )
            print(f"[RENDER DEBUG] Screen position: {screen_pos}")

            if (
                -TILE_SIZE < screen_pos[0] < screen.get_width()
                and -TILE_SIZE < screen_pos[1] < screen.get_height()
            ):
                print(f"[RENDER DEBUG] Building is visible, drawing...")
                width = building.size[0] * TILE_SIZE
                height = building.size[1] * TILE_SIZE

                color = (
                    COLORS["BROWN"]
                    if building.building_type.value == "TOWN_HALL"
                    else COLORS["GRAY"]
                )
                if building.player_id == self.network_manager.player_id:
                    color = COLORS["BLUE"]

                rect = pygame.Rect(screen_pos[0], screen_pos[1], width, height)
                pygame.draw.rect(screen, color, rect)
                pygame.draw.rect(screen, COLORS["WHITE"], rect, 2)
            else:
                print(f"[RENDER DEBUG] Building not visible (screen bounds: {screen.get_width()}x{screen.get_height()})")

    def _render_gathering_ranges(self, screen: pygame.Surface):
        """Render gathering ranges for resource buildings"""
        from shared.models.game_models import BuildingType

        # Define which building types are resource buildings
        resource_building_types = {
            BuildingType.FARM,
            BuildingType.WOOD_CUTTER,
            BuildingType.MINE,
            BuildingType.GOLD_MINE,
        }

        # Check if any resource building is selected (this will show ranges for all resource buildings)
        has_selected_resource_building = False
        if self.selected_entity:
            building_type = getattr(self.selected_entity, "building_type", None)
            has_selected_resource_building = building_type in resource_building_types

        if has_selected_resource_building:
            for building in self.game_state.buildings.values():
                if building.building_type not in resource_building_types:
                    continue

                if building.health <= 0:  # Skip destroyed buildings
                    continue

                is_selected = (
                    self.selected_entity
                    and hasattr(self.selected_entity, "id")
                    and self.selected_entity.id == building.id
                )

                self._render_single_gathering_range(screen, building, bool(is_selected))

    def _render_single_gathering_range(
        self, screen: pygame.Surface, building, is_selected: bool = False
    ):
        """Render gathering range for a single building"""
        # Calculate the gathering range area (5x5 tiles around building)
        range_size = 2  # 2 tiles in each direction (5x5 total)

        # Calculate the range boundaries in world coordinates
        range_left = building.position.x - range_size
        range_top = building.position.y - range_size
        range_right = building.position.x + building.size[0] + range_size
        range_bottom = building.position.y + building.size[1] + range_size

        # Convert to screen coordinates
        screen_left = int(range_left * TILE_SIZE - self.camera_x)
        screen_top = int(range_top * TILE_SIZE - self.camera_y)
        screen_right = int(range_right * TILE_SIZE - self.camera_x)
        screen_bottom = int(range_bottom * TILE_SIZE - self.camera_y)

        # Only render if visible on screen
        if (
            screen_right > 0
            and screen_left < screen.get_width()
            and screen_bottom > 0
            and screen_top < screen.get_height()
        ):

            # Create a transparent white surface for the range area
            range_width = screen_right - screen_left
            range_height = screen_bottom - screen_top

            if range_width > 0 and range_height > 0:
                # Use different opacity and color for selected vs all buildings
                if is_selected:
                    # Brighter and more visible for selected building
                    fill_color = (255, 255, 0, 80)  # Yellow with higher alpha
                    border_color = (255, 255, 0, 200)  # Bright yellow border
                    border_width = 3
                else:
                    # Subtle for non-selected buildings
                    fill_color = (255, 255, 255, 30)  # White with very low alpha
                    border_color = (255, 255, 255, 100)  # White border
                    border_width = 2

                # Create surface with transparent fill
                range_surface = pygame.Surface(
                    (range_width, range_height), pygame.SRCALPHA
                )
                range_surface.fill(fill_color)

                # Draw the filled area
                screen.blit(range_surface, (screen_left, screen_top))

                # Draw dotted border around the range
                self._draw_dotted_rect(
                    screen,
                    (screen_left, screen_top, range_width, range_height),
                    border_color,
                    border_width,
                    8,
                )

    def _draw_dotted_rect(
        self,
        surface: pygame.Surface,
        rect: tuple,
        color: tuple,
        width: int,
        dot_length: int,
    ):
        """Draw a dotted rectangle border"""
        x, y, w, h = rect

        # Draw dotted top edge
        for i in range(0, w, dot_length * 2):
            start_x = x + i
            end_x = min(x + i + dot_length, x + w)
            if start_x < end_x:
                pygame.draw.line(surface, color[:3], (start_x, y), (end_x, y), width)

        # Draw dotted bottom edge
        for i in range(0, w, dot_length * 2):
            start_x = x + i
            end_x = min(x + i + dot_length, x + w)
            if start_x < end_x:
                pygame.draw.line(
                    surface, color[:3], (start_x, y + h), (end_x, y + h), width
                )

        # Draw dotted left edge
        for i in range(0, h, dot_length * 2):
            start_y = y + i
            end_y = min(y + i + dot_length, y + h)
            if start_y < end_y:
                pygame.draw.line(surface, color[:3], (x, start_y), (x, end_y), width)

        # Draw dotted right edge
        for i in range(0, h, dot_length * 2):
            start_y = y + i
            end_y = min(y + i + dot_length, y + h)
            if start_y < end_y:
                pygame.draw.line(
                    surface, color[:3], (x + w, start_y), (x + w, end_y), width
                )

    def _render_heroes(self, screen: pygame.Surface):
        font = pygame.font.Font(None, 20)
        for hero in self.game_state.heroes.values():
            screen_pos = self._world_to_screen((hero.position.x, hero.position.y))

            if (
                -TILE_SIZE < screen_pos[0] < screen.get_width()
                and -TILE_SIZE < screen_pos[1] < screen.get_height()
            ):
                # Determine hero color based on ownership
                is_own_hero = hero.player_id == self.network_manager.player_id
                color = COLORS["GREEN"] if is_own_hero else COLORS["CYAN"]

                center_x = screen_pos[0] + TILE_SIZE // 2
                center_y = screen_pos[1] + TILE_SIZE // 2
                pygame.draw.circle(screen, color, (center_x, center_y), TILE_SIZE // 3)
                pygame.draw.circle(
                    screen, COLORS["WHITE"], (center_x, center_y), TILE_SIZE // 3, 2
                )

                # Render player name above hero
                player = self.game_state.players.get(hero.player_id)
                if player:
                    player_name = (
                        player.name if hasattr(player, "name") else hero.player_id[:8]
                    )
                    name_text = font.render(player_name, True, COLORS["WHITE"])
                    name_rect = name_text.get_rect()
                    name_rect.centerx = center_x
                    name_rect.bottom = center_y - TILE_SIZE // 3 - 5

                    # Draw background for name
                    bg_rect = name_rect.inflate(6, 2)
                    pygame.draw.rect(screen, (0, 0, 0, 128), bg_rect)
                    screen.blit(name_text, name_rect)

    def _render_pings(self, screen: pygame.Surface):
        """Render map pings/markers"""
        import time

        current_time = time.time()

        for ping in self.game_state.pings.values():
            # Check if ping is still active
            age = current_time - ping.timestamp
            if age >= ping.duration:
                continue

            screen_pos = self._world_to_screen((ping.position.x, ping.position.y))

            # Only render if on screen
            if (
                -50 < screen_pos[0] < screen.get_width() + 50
                and -50 < screen_pos[1] < screen.get_height() + 50
            ):
                center_x = screen_pos[0] + TILE_SIZE // 2
                center_y = screen_pos[1] + TILE_SIZE // 2

                # Calculate fade effect based on age
                fade_factor = 1.0 - (age / ping.duration)
                alpha = int(255 * fade_factor)

                # Get ping color based on type (matching radial menu colors)
                from shared.models.game_models import PingType

                if ping.ping_type == PingType.ATTENTION:
                    base_color = (255, 255, 0)  # Yellow
                elif ping.ping_type == PingType.DANGER:
                    base_color = (255, 0, 0)  # Red
                elif ping.ping_type == PingType.HELP:
                    base_color = (0, 255, 0)  # Green
                elif ping.ping_type == PingType.MOVE_HERE:
                    base_color = (0, 150, 255)  # Blue
                else:
                    base_color = (255, 255, 255)  # White fallback

                # Create animated ping effect
                ping_radius = int(20 + 10 * math.sin(age * 8))  # Pulsing animation

                # Draw outer ring
                pygame.draw.circle(
                    screen,
                    (*base_color, max(50, alpha // 2)),
                    (center_x, center_y),
                    ping_radius,
                    3,
                )
                # Draw inner circle
                pygame.draw.circle(
                    screen, (*base_color, alpha), (center_x, center_y), 8
                )

                # Draw player name who created the ping
                font = pygame.font.Font(None, 16)
                name_text = font.render(ping.player_name, True, (255, 255, 255, alpha))
                name_rect = name_text.get_rect()
                name_rect.centerx = center_x
                name_rect.top = center_y + 25

                # Draw background for name
                bg_rect = name_rect.inflate(4, 2)
                pygame.draw.rect(screen, (0, 0, 0, min(200, alpha)), bg_rect)
                screen.blit(name_text, name_rect)

    def _render_attack_effects(self, screen: pygame.Surface):
        """Render attack effects/animations"""
        import time

        current_time = time.time()

        for effect in self.game_state.attack_effects.values():
            # Check if effect is still active
            age = current_time - effect.start_time
            if age >= effect.duration:
                continue

            # Calculate animation progress (0.0 to 1.0)
            progress = age / effect.duration

            start_screen_pos = self._world_to_screen(
                (effect.start_position.x, effect.start_position.y)
            )
            end_screen_pos = self._world_to_screen(
                (effect.end_position.x, effect.end_position.y)
            )

            # Only render if on screen
            if (
                -50 < start_screen_pos[0] < screen.get_width() + 50
                and -50 < start_screen_pos[1] < screen.get_height() + 50
            ) or (
                -50 < end_screen_pos[0] < screen.get_width() + 50
                and -50 < end_screen_pos[1] < screen.get_height() + 50
            ):
                start_x = start_screen_pos[0] + TILE_SIZE // 2
                start_y = start_screen_pos[1] + TILE_SIZE // 2
                end_x = end_screen_pos[0] + TILE_SIZE // 2
                end_y = end_screen_pos[1] + TILE_SIZE // 2

                if effect.effect_type.value == "MELEE":
                    # Melee attack: flash effect at target position
                    alpha = int(255 * (1.0 - progress))
                    flash_color = (255, 255, 100, alpha)
                    pygame.draw.circle(
                        screen, flash_color, (end_x, end_y), int(20 * (1.0 - progress))
                    )

                elif effect.effect_type.value == "RANGED":
                    # Ranged attack: projectile traveling from start to end
                    current_x = int(start_x + (end_x - start_x) * progress)
                    current_y = int(start_y + (end_y - start_y) * progress)
                    pygame.draw.circle(
                        screen, COLORS["YELLOW"], (current_x, current_y), 3
                    )
                    # Draw arrow trail
                    if progress > 0.1:
                        trail_length = 10
                        trail_x = int(current_x - (end_x - start_x) * 0.1)
                        trail_y = int(current_y - (end_y - start_y) * 0.1)
                        pygame.draw.line(
                            screen,
                            COLORS["ORANGE"],
                            (trail_x, trail_y),
                            (current_x, current_y),
                            2,
                        )

                elif effect.effect_type.value == "MAGIC":
                    # Magic attack: expanding magical effect
                    alpha = int(255 * (1.0 - progress))
                    magic_color = (150, 100, 255, alpha)
                    radius = int(15 + 10 * progress)
                    pygame.draw.circle(screen, magic_color, (end_x, end_y), radius, 2)
                    # Add sparkle effect
                    for i in range(5):
                        angle = (progress * 360 + i * 72) % 360
                        sparkle_x = int(
                            end_x + math.cos(math.radians(angle)) * radius * 0.7
                        )
                        sparkle_y = int(
                            end_y + math.sin(math.radians(angle)) * radius * 0.7
                        )
                        pygame.draw.circle(
                            screen, (255, 255, 255, alpha), (sparkle_x, sparkle_y), 2
                        )

    def _render_enemies(self, screen: pygame.Surface):
        for enemy in self.game_state.enemies.values():
            screen_pos = self._world_to_screen((enemy.position.x, enemy.position.y))

            if (
                -TILE_SIZE < screen_pos[0] < screen.get_width()
                and -TILE_SIZE < screen_pos[1] < screen.get_height()
            ):
                center_x = screen_pos[0] + TILE_SIZE // 2
                center_y = screen_pos[1] + TILE_SIZE // 2

                # Choose color based on dead state
                if enemy.is_dead:
                    # Dead enemy: dark grey-red color
                    enemy_color = (80, 40, 40)  # Dark grey-red
                    border_color = (120, 60, 60)  # Slightly lighter grey-red
                else:
                    # Alive enemy: normal red
                    enemy_color = COLORS["RED"]
                    border_color = COLORS["WHITE"]

                pygame.draw.circle(
                    screen, enemy_color, (center_x, center_y), TILE_SIZE // 4
                )
                pygame.draw.circle(
                    screen, border_color, (center_x, center_y), TILE_SIZE // 4, 1
                )

    def _render_fog_of_war(self, screen: pygame.Surface):
        fog_rect = pygame.Rect(
            -int(self.camera_x),
            -int(self.camera_y),
            MAP_WIDTH * TILE_SIZE,
            MAP_HEIGHT * TILE_SIZE,
        )
        screen.blit(self.fog_surface, fog_rect)

    def _open_esc_menu(self):
        """Open the ESC menu and pause the game"""
        self.esc_menu_open = True
        # Send pause request to server
        asyncio.create_task(
            self.network_manager.send_game_action({"type": "toggle_pause"})
        )

    def _close_esc_menu(self):
        """Close the ESC menu and unpause the game"""
        self.esc_menu_open = False
        # Send unpause request to server (if game is paused)
        if self.game_state.is_paused:
            asyncio.create_task(
                self.network_manager.send_game_action({"type": "toggle_pause"})
            )

    def _quit_to_menu(self):
        """Quit to main menu"""

        self.next_scene = MenuScene(self.screen, self.network_manager)

    def _is_click_in_esc_menu(self, pos: tuple) -> bool:
        """Check if click is within the ESC menu area"""
        menu_rect = pygame.Rect(350, 200, 300, 200)
        return menu_rect.collidepoint(pos)

    def _render_esc_menu(self, screen: pygame.Surface):
        """Render the ESC menu overlay"""
        # Semi-transparent overlay
        overlay = pygame.Surface((screen.get_width(), screen.get_height()))
        overlay.set_alpha(128)
        overlay.fill(COLORS["BLACK"])
        screen.blit(overlay, (0, 0))

        # Menu background
        menu_rect = pygame.Rect(350, 200, 300, 200)
        pygame.draw.rect(screen, COLORS["DARK_GRAY"], menu_rect)
        pygame.draw.rect(screen, COLORS["WHITE"], menu_rect, 3)

        # Title
        title_text = self.font.render("PAUSED", True, COLORS["WHITE"])
        title_rect = title_text.get_rect(center=(500, 230))
        screen.blit(title_text, title_rect)

        # Continue button
        continue_color = COLORS["GREEN"]
        pygame.draw.rect(screen, continue_color, self.esc_menu_buttons["continue"])
        pygame.draw.rect(screen, COLORS["WHITE"], self.esc_menu_buttons["continue"], 2)
        continue_text = self.small_font.render("Continue", True, COLORS["WHITE"])
        continue_rect = continue_text.get_rect(
            center=self.esc_menu_buttons["continue"].center
        )
        screen.blit(continue_text, continue_rect)

        # Quit to menu button
        quit_color = COLORS["RED"]
        pygame.draw.rect(screen, quit_color, self.esc_menu_buttons["quit_to_menu"])
        pygame.draw.rect(
            screen, COLORS["WHITE"], self.esc_menu_buttons["quit_to_menu"], 2
        )
        quit_text = self.small_font.render("Quit to Menu", True, COLORS["WHITE"])
        quit_rect = quit_text.get_rect(
            center=self.esc_menu_buttons["quit_to_menu"].center
        )
        screen.blit(quit_text, quit_rect)

    def _render_grid(self, screen: pygame.Surface):
        """Render the pathfinding grid overlay"""
        start_x = max(0, int(self.camera_x) // TILE_SIZE)
        start_y = max(0, int(self.camera_y) // TILE_SIZE)
        end_x = min(
            MAP_WIDTH, (int(self.camera_x) + screen.get_width()) // TILE_SIZE + 1
        )
        end_y = min(
            MAP_HEIGHT, (int(self.camera_y) + screen.get_height()) // TILE_SIZE + 1
        )

        # Draw grid lines
        grid_color = (100, 100, 100, 128)  # Semi-transparent gray

        # Vertical lines
        for x in range(start_x, end_x + 1):
            screen_x = x * TILE_SIZE - int(self.camera_x)
            if 0 <= screen_x <= screen.get_width():
                pygame.draw.line(
                    screen,
                    grid_color[:3],
                    (screen_x, 0),
                    (screen_x, screen.get_height()),
                    1,
                )

        # Horizontal lines
        for y in range(start_y, end_y + 1):
            screen_y = y * TILE_SIZE - int(self.camera_y)
            if 0 <= screen_y <= screen.get_height():
                pygame.draw.line(
                    screen,
                    grid_color[:3],
                    (0, screen_y),
                    (screen.get_width(), screen_y),
                    1,
                )

        # Draw grid center dots to show tile centers
        dot_color = (150, 150, 150)
        for y in range(start_y, end_y):
            for x in range(start_x, end_x):
                center_x = x * TILE_SIZE + TILE_SIZE // 2 - int(self.camera_x)
                center_y = y * TILE_SIZE + TILE_SIZE // 2 - int(self.camera_y)
                if (
                    0 <= center_x <= screen.get_width()
                    and 0 <= center_y <= screen.get_height()
                ):
                    pygame.draw.circle(screen, dot_color, (center_x, center_y), 2)

    def _render_waypoints(self, screen: pygame.Surface):
        """Render hero waypoints and paths"""
        # Check if we have hero paths data from server (we'll need to add this)
        # For now, let's request this information from the server

        # Draw waypoints for each hero
        for hero in self.game_state.heroes.values():
            if hero.player_id == self.network_manager.player_id:
                # Draw current hero position
                hero_screen_pos = self._world_to_screen(
                    (hero.position.x, hero.position.y)
                )
                center_x = hero_screen_pos[0] + TILE_SIZE // 2
                center_y = hero_screen_pos[1] + TILE_SIZE // 2

                # Draw hero position marker
                pygame.draw.circle(screen, (0, 255, 0), (center_x, center_y), 8, 3)

                # For now, we'll simulate some waypoints to show the system works
                # In a real implementation, we'd get this from the server
                if hasattr(hero, "path_waypoints"):
                    # Draw path waypoints
                    waypoint_color = (255, 255, 0)  # Yellow
                    path_color = (255, 255, 0, 128)  # Semi-transparent yellow

                    prev_pos = (center_x, center_y)
                    for i, waypoint in enumerate(hero.path_waypoints):
                        waypoint_screen_pos = self._world_to_screen(
                            (waypoint.x, waypoint.y)
                        )
                        wp_x = waypoint_screen_pos[0] + TILE_SIZE // 2
                        wp_y = waypoint_screen_pos[1] + TILE_SIZE // 2

                        # Draw line to previous waypoint
                        pygame.draw.line(
                            screen, path_color[:3], prev_pos, (wp_x, wp_y), 3
                        )

                        # Draw waypoint marker
                        pygame.draw.circle(screen, waypoint_color, (wp_x, wp_y), 6)

                        # Draw waypoint number
                        font = pygame.font.Font(None, 16)
                        text = font.render(str(i), True, (0, 0, 0))
                        text_rect = text.get_rect(center=(wp_x, wp_y))
                        screen.blit(text, text_rect)

                        prev_pos = (wp_x, wp_y)

        # Add debug info about which pathfinding system is being used
        font = pygame.font.Font(None, 24)
        debug_text = "Pathfinding Debug: F1=Grid, F2=Waypoints"
        text_surface = font.render(debug_text, True, (255, 255, 255))
        text_rect = text_surface.get_rect()
        text_rect.bottomleft = (10, screen.get_height() - 10)

        # Draw background
        bg_rect = text_rect.inflate(10, 4)
        pygame.draw.rect(screen, (0, 0, 0, 180), bg_rect)
        screen.blit(text_surface, text_rect)

    def _check_hero_arrival_for_pending_build(self):
        """Check if hero has arrived at pending build location and auto-build"""
        if not self.pending_build:
            return

        # Get the current player's hero
        player_id = self.network_manager.player_id
        hero = None
        for h in self.game_state.heroes.values():
            if h.player_id == player_id:
                hero = h
                break

        if not hero:
            return

        # Check if hero is adjacent to pending build position
        pending_pos = self.pending_build["position"]
        building_type = self.pending_build["building_type"]
        from shared.constants.game_constants import BUILDING_TYPES

        # Get building size
        building_info = BUILDING_TYPES.get(building_type)
        if not building_info:
            return
        size = building_info["size"]

        # Convert coordinates to tiles
        hero_tile_x = int(hero.position.x)  # Hero position is in tile coordinates
        hero_tile_y = int(hero.position.y)
        # Convert building position from pixels to tiles
        from shared.constants.game_constants import TILE_SIZE
        building_tile_x = int(pending_pos["x"] // TILE_SIZE)
        building_tile_y = int(pending_pos["y"] // TILE_SIZE)

        # Check if hero touches any border of the building area
        # Hero needs to be within 1 tile of the building's edge
        is_adjacent = False
        min_distance_found = float("inf")
        for bx in range(building_tile_x, building_tile_x + size[0]):
            for by in range(building_tile_y, building_tile_y + size[1]):
                distance = math.sqrt((hero_tile_x - bx) ** 2 + (hero_tile_y - by) ** 2)
                min_distance_found = min(min_distance_found, distance)
                if distance <= 1.8:  # Slightly more lenient to match server threshold
                    is_adjacent = True
                    break
            if is_adjacent:
                break

        if is_adjacent:
            print(f"🏗️ Hero reached building border! Auto-constructing {building_type}")
            print(
                f"📍 Hero at ({hero_tile_x}, {hero_tile_y}), Building at ({building_tile_x}, {building_tile_y}) size {size}"
            )
            print(f"🔍 Min distance found: {min_distance_found:.2f}")
            print(f"📦 Sending build command: {self.pending_build}")
            print(f"[CLIENT DEBUG] 🚀 Sending auto-build: {self.pending_build['building_type']} at pixel coords ({self.pending_build['position']['x']}, {self.pending_build['position']['y']})")
            # Send the build command
            asyncio.create_task(
                self.network_manager.send_game_action(self.pending_build)
            )
            # Clear the pending build and stop travel state
            self.pending_build = None
            self.building_placer.set_hero_traveling(False)
            self.building_placer.stop_placement()
            self.building_menu.clear_selection()
            print("✅ Auto-build command sent and states cleared")
        else:
            print(f"❌ Hero NOT adjacent! Distance: {min_distance_found:.2f} (need <= 1.8)")
            print(f"📍 Hero at ({hero_tile_x}, {hero_tile_y}), Building at ({building_tile_x}, {building_tile_y}) size {size}")

    def get_next_scene(self):
        if self.next_scene:
            print(
                f"[DEBUG] get_next_scene called - returning: {type(self.next_scene).__name__}"
            )
            next_scene = self.next_scene
            self.next_scene = None
            return next_scene
        return None

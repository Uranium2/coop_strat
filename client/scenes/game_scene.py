import asyncio
import math
from typing import Any, Dict, Optional

import pygame

from client.scenes.menu_scene import MenuScene
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
from shared.models.game_models import GameState, TileType


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
        self.resource_panel = ResourcePanel(
            screen.get_width() - 300, screen.get_height() - 100, 280, 80
        )
        self.selection_panel = SelectionPanel(
            screen.get_width() // 2 - 150, screen.get_height() - 120, 300, 100
        )
        self.radial_ping_menu = RadialPingMenu()

        # Track CTRL key state for ping menu
        self.ctrl_pressed = False

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

        self.network_manager.register_handler("game_update", self._on_game_update)
        self.network_manager.register_handler("hero_moved", self._on_hero_moved)
        self.network_manager.register_handler(
            "building_placed", self._on_building_placed
        )

        self._update_fog_of_war()

    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if self.radial_ping_menu.is_active:
                    self.radial_ping_menu.deactivate()
                elif self.build_mode:
                    self.build_mode = None
                else:
                    from client.scenes.menu_scene import MenuScene

                    self.next_scene = MenuScene(self.screen, self.network_manager)
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
                    if self.build_mode:
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
                return

        self.selected_entity = None

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

        # Check if mouse is over resource panel
        if (
            screen_width - 300 <= x <= screen_width
            and screen_height - 100 <= y <= screen_height
        ):
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
        self.game_state = GameState(**data["game_state"])
        self._update_fog_of_war()

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
        # Handle continuous arrow key camera movement
        self._handle_continuous_camera_movement()

        # Handle mouse edge scrolling
        self._handle_mouse_edge_scrolling()

    def render(self, screen: pygame.Surface):
        screen.fill(COLORS["BLACK"])

        self._render_map(screen)
        self._render_buildings(screen)
        self._render_enemies(screen)
        self._render_fog_of_war(screen)
        # Render heroes AFTER fog of war so they're always visible
        self._render_heroes(screen)
        # Render pings on top of everything else in the game world
        self._render_pings(screen)

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

    def _render_build_info(self, screen: pygame.Surface):
        font = pygame.font.Font(None, 24)
        text = f"Build Mode: {self.build_mode} (Right-click to cancel)"
        text_surface = font.render(text, True, COLORS["WHITE"])
        screen.blit(text_surface, (10, 10))

    def _render_lobby_info(self, screen: pygame.Surface):
        font = pygame.font.Font(None, 24)
        lobby_id = getattr(self.game_state, "lobby_id", "Unknown")
        if lobby_id:
            # Display lobby ID at the top center of screen
            text = (
                f"Lobby: {lobby_id[:12]}..."
                if len(lobby_id) > 15
                else f"Lobby: {lobby_id}"
            )
            text_surface = font.render(text, True, COLORS["CYAN"])
            text_rect = text_surface.get_rect()
            text_rect.centerx = screen.get_width() // 2
            text_rect.y = 10

            # Draw background for better visibility
            bg_rect = text_rect.inflate(20, 10)
            pygame.draw.rect(screen, (0, 0, 0, 128), bg_rect)
            pygame.draw.rect(screen, COLORS["WHITE"], bg_rect, 1)

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
                        color = self.tile_colors.get(tile_type, COLORS["BLACK"])
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
        for building in self.game_state.buildings.values():
            screen_pos = self._world_to_screen(
                (building.position.x, building.position.y)
            )

            if (
                -TILE_SIZE < screen_pos[0] < screen.get_width()
                and -TILE_SIZE < screen_pos[1] < screen.get_height()
            ):
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

    def _render_enemies(self, screen: pygame.Surface):
        for enemy in self.game_state.enemies.values():
            screen_pos = self._world_to_screen((enemy.position.x, enemy.position.y))

            if (
                -TILE_SIZE < screen_pos[0] < screen.get_width()
                and -TILE_SIZE < screen_pos[1] < screen.get_height()
            ):
                center_x = screen_pos[0] + TILE_SIZE // 2
                center_y = screen_pos[1] + TILE_SIZE // 2
                pygame.draw.circle(
                    screen, COLORS["RED"], (center_x, center_y), TILE_SIZE // 4
                )
                pygame.draw.circle(
                    screen, COLORS["WHITE"], (center_x, center_y), TILE_SIZE // 4, 1
                )

    def _render_fog_of_war(self, screen: pygame.Surface):
        fog_rect = pygame.Rect(
            -int(self.camera_x),
            -int(self.camera_y),
            MAP_WIDTH * TILE_SIZE,
            MAP_HEIGHT * TILE_SIZE,
        )
        screen.blit(self.fog_surface, fog_rect)

    def get_next_scene(self) -> Optional["MenuScene"]:
        if self.next_scene:
            next_scene = self.next_scene
            self.next_scene = None
            return next_scene
        return None

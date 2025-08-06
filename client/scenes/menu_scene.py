import pygame
import asyncio
import logging
from typing import Optional
from client.utils.network_manager import NetworkManager
from shared.constants.game_constants import COLORS

logger = logging.getLogger(__name__)


class MenuScene:
    def __init__(self, screen: pygame.Surface, network_manager: NetworkManager):
        self.screen = screen
        self.network_manager = network_manager
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)

        self.state = "main_menu"
        self.input_text = ""
        self.lobby_id = ""
        self.player_name = "Player"
        self.selected_hero = "TANK"
        self.next_scene = None

        logger.info("MenuScene initialized")

        self.buttons = {
            "create_lobby": pygame.Rect(400, 300, 200, 50),
            "join_lobby": pygame.Rect(400, 370, 200, 50),
            "quit": pygame.Rect(400, 440, 200, 50),
            "back": pygame.Rect(50, 50, 100, 40),
            "refresh": pygame.Rect(750, 50, 100, 40),
        }

        self.hero_buttons = {
            "TANK": pygame.Rect(300, 200, 100, 50),
            "BUILDER": pygame.Rect(420, 200, 100, 50),
            "ARCHER": pygame.Rect(540, 200, 100, 50),
            "MAGE": pygame.Rect(660, 200, 100, 50),
        }

        self.network_manager.register_handler("lobby_created", self._on_lobby_created)
        self.network_manager.register_handler("player_joined", self._on_player_joined)
        self.network_manager.register_handler("hero_selected", self._on_hero_selected)
        self.network_manager.register_handler("game_started", self._on_game_started)
        self.network_manager.register_handler("join_failed", self._on_join_failed)
        self.network_manager.register_handler("lobby_list", self._on_lobby_list)

        self.available_lobbies = []
        self.lobby_list_refresh_timer = 0
        self.lobby_list_refresh_interval = 3.0  # Refresh every 3 seconds

        logger.info("All message handlers registered")

    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.KEYDOWN:
            # ESC key to go back to main menu from input states
            if event.key == pygame.K_ESCAPE and self.state in ["enter_name", "enter_lobby_id", "lobby_browser"]:
                logger.info("ESC pressed, returning to main menu")
                self.state = "main_menu"
                self.input_text = ""
                self.lobby_id = ""  # Reset lobby_id when going back
                return
            
            if self.state == "enter_name":
                if event.key == pygame.K_RETURN:
                    self.player_name = self.input_text if self.input_text else "Player"
                    if self.lobby_id:  # If we're joining a specific lobby
                        self.state = "connecting"
                        asyncio.create_task(self._connect_and_join_lobby())
                    else:  # If we're creating a new lobby
                        self.state = "connecting"
                        asyncio.create_task(self._connect_to_server())
                elif event.key == pygame.K_BACKSPACE:
                    self.input_text = self.input_text[:-1]
                else:
                    self.input_text += event.unicode

            elif self.state == "enter_lobby_id":
                if event.key == pygame.K_RETURN:
                    if self.input_text:
                        self.lobby_id = self.input_text
                        self.state = "connecting"
                        asyncio.create_task(self._connect_and_join_lobby())
                elif event.key == pygame.K_BACKSPACE:
                    self.input_text = self.input_text[:-1]
                else:
                    self.input_text += event.unicode

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                self._handle_click(event.pos)

    def _handle_click(self, pos: tuple):
        logger.debug(f"Click detected at {pos} in state {self.state}")
        
        # Handle back button for states that need it
        if self.state in ["enter_name", "enter_lobby_id", "lobby_browser"] and self.buttons["back"].collidepoint(pos):
            logger.info("Back button clicked, returning to main menu")
            self.state = "main_menu"
            self.input_text = ""
            self.lobby_id = ""  # Reset lobby_id when going back
            return
        
        if self.state == "main_menu":
            if self.buttons["create_lobby"].collidepoint(pos):
                logger.info("Create lobby button clicked")
                self.state = "enter_name"
                self.input_text = ""
            elif self.buttons["join_lobby"].collidepoint(pos):
                logger.info("Browse lobbies button clicked - showing lobby browser")
                self.state = "connecting"
                asyncio.create_task(self._connect_and_browse_lobbies())
            elif self.buttons["quit"].collidepoint(pos):
                logger.info("Quit button clicked")
                pygame.quit()
                exit()

        elif self.state == "lobby_browser":
            # Handle refresh button
            if self.buttons["refresh"].collidepoint(pos):
                logger.info("Refresh button clicked")
                if self.network_manager.is_connected():
                    asyncio.create_task(self.network_manager.list_lobbies())
            
            # Handle lobby selection
            for i, lobby in enumerate(self.available_lobbies):
                lobby_rect = pygame.Rect(200, 150 + i * 70, 600, 60)
                if lobby_rect.collidepoint(pos):
                    # Only allow joining if lobby is not in active game
                    status = lobby.get("status", "waiting")
                    if status == "in_game":
                        logger.info(f"Cannot join lobby {lobby['lobby_id']} - game in progress")
                        # TODO: Could show a message to user here
                        return
                    elif status == "full":
                        logger.info(f"Cannot join lobby {lobby['lobby_id']} - lobby full")
                        # TODO: Could show a message to user here  
                        return
                    else:
                        logger.info(f"Joining lobby {lobby['lobby_id']}")
                        self.lobby_id = lobby["lobby_id"]
                        self.state = "enter_name"  # Ask for player name before joining
                        self.input_text = ""

        elif self.state == "lobby":
            for hero_type, rect in self.hero_buttons.items():
                if rect.collidepoint(pos):
                    logger.info(f"Hero {hero_type} selected")
                    self.selected_hero = hero_type
                    asyncio.create_task(self.network_manager.select_hero(hero_type))

            start_button = pygame.Rect(400, 350, 200, 50)
            if start_button.collidepoint(pos):
                logger.info("Start game button clicked")
                asyncio.create_task(self.network_manager.start_game())

    async def _connect_to_server(self):
        logger.info("Attempting to connect to server")
        if await self.network_manager.connect():
            logger.info("Connected successfully, creating lobby")
            await self.network_manager.create_lobby(self.player_name)
        else:
            logger.error("Failed to connect to server")
            self.state = "connection_failed"

    async def _connect_and_join_lobby(self):
        logger.info("Attempting to connect to server and join lobby")
        if await self.network_manager.connect():
            logger.info("Connected successfully, joining lobby")
            await self.network_manager.join_lobby(self.lobby_id, self.player_name)
        else:
            logger.error("Failed to connect to server")
            self.state = "connection_failed"

    async def _connect_and_browse_lobbies(self):
        logger.info("Attempting to connect to server and browse lobbies")
        if await self.network_manager.connect():
            logger.info("Connected successfully, requesting lobby list")
            await self.network_manager.list_lobbies()
        else:
            logger.error("Failed to connect to server")
            self.state = "connection_failed"

    def _on_lobby_list(self, data):
        logger.info(f"Received lobby list: {data}")
        self.available_lobbies = data.get("lobbies", [])
        self.state = "lobby_browser"

    def _on_lobby_created(self, data):
        logger.info(f"Lobby created: {data}")
        self.lobby_id = data["lobby_id"]
        self.state = "lobby"
        # Automatically select the default hero
        logger.info(f"Auto-selecting default hero: {self.selected_hero}")
        asyncio.create_task(self.network_manager.select_hero(self.selected_hero))

    def _on_player_joined(self, data):
        logger.info(f"Player joined: {data}")
        if data.get("player_id") == self.network_manager.player_id:
            # We successfully joined a lobby
            self.state = "lobby"
            # Automatically select the default hero
            logger.info(f"Auto-selecting default hero: {self.selected_hero}")
            asyncio.create_task(self.network_manager.select_hero(self.selected_hero))

    def _on_hero_selected(self, data):
        logger.info(f"Hero selected: {data}")

    def _on_game_started(self, data):
        logger.info("Game started, switching to game scene")
        try:
            from client.scenes.game_scene import GameScene
            game_state = data["game_state"]
            logger.info(f"Creating GameScene with game state keys: {list(game_state.keys())}")
            
            self.next_scene = GameScene(
                self.screen, self.network_manager, game_state
            )
            logger.info("GameScene created successfully")
        except Exception as e:
            logger.error(f"Failed to create GameScene: {e}", exc_info=True)
            # Stay in lobby if game scene creation fails
            self.state = "lobby"

    def _on_join_failed(self, data):
        logger.warning(f"Join failed: {data}")
        self.state = "connection_failed"

    def update(self, dt: float):
        # Auto-refresh lobby list when browsing
        if self.state == "lobby_browser":
            self.lobby_list_refresh_timer += dt
            if self.lobby_list_refresh_timer >= self.lobby_list_refresh_interval:
                self.lobby_list_refresh_timer = 0
                if self.network_manager.is_connected():
                    asyncio.create_task(self.network_manager.list_lobbies())

    def render(self, screen: pygame.Surface):
        screen.fill(COLORS["BLACK"])

        if self.state == "main_menu":
            self._render_main_menu(screen)
        elif self.state == "enter_name":
            self._render_name_input(screen)
        elif self.state == "enter_lobby_id":
            self._render_lobby_id_input(screen)
        elif self.state == "connecting":
            self._render_connecting(screen)
        elif self.state == "lobby_browser":
            self._render_lobby_browser(screen)
        elif self.state == "lobby":
            self._render_lobby(screen)
        elif self.state == "connection_failed":
            self._render_connection_failed(screen)

    def _render_main_menu(self, screen: pygame.Surface):
        title = self.font.render("Co-op Survival RTS", True, COLORS["WHITE"])
        title_rect = title.get_rect(center=(screen.get_width() // 2, 150))
        screen.blit(title, title_rect)

        for text, rect in [
            ("Create Lobby", self.buttons["create_lobby"]),
            ("Browse Lobbies", self.buttons["join_lobby"]),
            ("Quit", self.buttons["quit"]),
        ]:
            pygame.draw.rect(screen, COLORS["GRAY"], rect)
            pygame.draw.rect(screen, COLORS["WHITE"], rect, 2)

            text_surf = self.small_font.render(text, True, COLORS["WHITE"])
            text_rect = text_surf.get_rect(center=rect.center)
            screen.blit(text_surf, text_rect)
            
        # Instructions
        instruction_text = self.small_font.render("'Browse Lobbies' shows available lobbies for joining", True, COLORS["GRAY"])
        instruction_rect = instruction_text.get_rect(center=(screen.get_width() // 2, 500))
        screen.blit(instruction_text, instruction_rect)

    def _render_name_input(self, screen: pygame.Surface):
        if self.lobby_id:
            prompt = self.font.render(f"Enter your name to join lobby:", True, COLORS["WHITE"])
            lobby_text = self.small_font.render(f"Lobby: {self.lobby_id[:8]}...", True, COLORS["CYAN"])
        else:
            prompt = self.font.render("Enter your name:", True, COLORS["WHITE"])
            lobby_text = None
            
        prompt_rect = prompt.get_rect(center=(screen.get_width() // 2, 180))
        screen.blit(prompt, prompt_rect)
        
        if lobby_text:
            lobby_rect = lobby_text.get_rect(center=(screen.get_width() // 2, 210))
            screen.blit(lobby_text, lobby_rect)

        input_rect = pygame.Rect(300, 250, 400, 40)
        pygame.draw.rect(screen, COLORS["WHITE"], input_rect)
        pygame.draw.rect(screen, COLORS["BLACK"], input_rect, 2)

        text_surf = self.small_font.render(self.input_text, True, COLORS["BLACK"])
        screen.blit(text_surf, (input_rect.x + 5, input_rect.y + 10))

        # Back button
        pygame.draw.rect(screen, COLORS["RED"], self.buttons["back"])
        pygame.draw.rect(screen, COLORS["WHITE"], self.buttons["back"], 2)
        back_text = self.small_font.render("Back", True, COLORS["WHITE"])
        back_text_rect = back_text.get_rect(center=self.buttons["back"].center)
        screen.blit(back_text, back_text_rect)

    def _render_lobby_id_input(self, screen: pygame.Surface):
        prompt = self.font.render("Enter lobby ID:", True, COLORS["WHITE"])
        prompt_rect = prompt.get_rect(center=(screen.get_width() // 2, 200))
        screen.blit(prompt, prompt_rect)

        input_rect = pygame.Rect(300, 250, 400, 40)
        pygame.draw.rect(screen, COLORS["WHITE"], input_rect)
        pygame.draw.rect(screen, COLORS["BLACK"], input_rect, 2)

        text_surf = self.small_font.render(self.input_text, True, COLORS["BLACK"])
        screen.blit(text_surf, (input_rect.x + 5, input_rect.y + 10))

        # Back button
        pygame.draw.rect(screen, COLORS["RED"], self.buttons["back"])
        pygame.draw.rect(screen, COLORS["WHITE"], self.buttons["back"], 2)
        back_text = self.small_font.render("Back", True, COLORS["WHITE"])
        back_text_rect = back_text.get_rect(center=self.buttons["back"].center)
        screen.blit(back_text, back_text_rect)

    def _render_connecting(self, screen: pygame.Surface):
        text = self.font.render("Connecting to server...", True, COLORS["WHITE"])
        text_rect = text.get_rect(
            center=(screen.get_width() // 2, screen.get_height() // 2)
        )
        screen.blit(text, text_rect)

    def _render_lobby(self, screen: pygame.Surface):
        title = self.font.render("Lobby", True, COLORS["WHITE"])
        title_rect = title.get_rect(center=(screen.get_width() // 2, 80))
        screen.blit(title, title_rect)
        
        # Display lobby ID
        lobby_id_text = self.small_font.render(f"Lobby ID: {self.lobby_id}", True, COLORS["CYAN"])
        lobby_id_rect = lobby_id_text.get_rect(center=(screen.get_width() // 2, 110))
        screen.blit(lobby_id_text, lobby_id_rect)
        
        # Instructions
        instructions = self.small_font.render("Share this Lobby ID with friends to let them join!", True, COLORS["GRAY"])
        instructions_rect = instructions.get_rect(center=(screen.get_width() // 2, 130))
        screen.blit(instructions, instructions_rect)

        hero_text = self.small_font.render("Select Hero:", True, COLORS["WHITE"])
        screen.blit(hero_text, (300, 170))

        for hero_type, rect in self.hero_buttons.items():
            color = (
                COLORS["GREEN"] if hero_type == self.selected_hero else COLORS["GRAY"]
            )
            pygame.draw.rect(screen, color, rect)
            pygame.draw.rect(screen, COLORS["WHITE"], rect, 2)

            text_surf = self.small_font.render(hero_type, True, COLORS["WHITE"])
            text_rect = text_surf.get_rect(center=rect.center)
            screen.blit(text_surf, text_rect)

        start_button = pygame.Rect(400, 350, 200, 50)
        pygame.draw.rect(screen, COLORS["GREEN"], start_button)
        pygame.draw.rect(screen, COLORS["WHITE"], start_button, 2)

        start_text = self.small_font.render("Start Game", True, COLORS["WHITE"])
        start_text_rect = start_text.get_rect(center=start_button.center)
        screen.blit(start_text, start_text_rect)

    def _render_lobby_browser(self, screen: pygame.Surface):
        title = self.font.render("Browse & Join Lobbies", True, COLORS["WHITE"])
        title_rect = title.get_rect(center=(screen.get_width() // 2, 80))
        screen.blit(title, title_rect)

        # Refresh button
        pygame.draw.rect(screen, COLORS["BLUE"], self.buttons["refresh"])
        pygame.draw.rect(screen, COLORS["WHITE"], self.buttons["refresh"], 2)
        refresh_text = self.small_font.render("Refresh", True, COLORS["WHITE"])
        refresh_text_rect = refresh_text.get_rect(center=self.buttons["refresh"].center)
        screen.blit(refresh_text, refresh_text_rect)



        # Auto-refresh indicator
        refresh_progress = 1.0 - (self.lobby_list_refresh_timer / self.lobby_list_refresh_interval)
        refresh_bar_width = int(100 * refresh_progress)
        refresh_bar = pygame.Rect(750, 100, refresh_bar_width, 5)
        pygame.draw.rect(screen, COLORS["GREEN"], refresh_bar)

        if not self.available_lobbies:
            no_lobbies_text = self.small_font.render(
                "No lobbies available", True, COLORS["GRAY"]
            )
            no_lobbies_rect = no_lobbies_text.get_rect(
                center=(screen.get_width() // 2, 300)
            )
            screen.blit(no_lobbies_text, no_lobbies_rect)
            
            hint_text = self.small_font.render(
                "Create a lobby or wait for others to create one", True, COLORS["GRAY"]
            )
            hint_rect = hint_text.get_rect(
                center=(screen.get_width() // 2, 330)
            )
            screen.blit(hint_text, hint_rect)
        else:
            # Header
            header_y = 120
            header_text = self.small_font.render("Lobby ID", True, COLORS["WHITE"])
            screen.blit(header_text, (220, header_y))
            header_text = self.small_font.render("Players", True, COLORS["WHITE"])
            screen.blit(header_text, (500, header_y))
            header_text = self.small_font.render("Status", True, COLORS["WHITE"])
            screen.blit(header_text, (600, header_y))
            
            for i, lobby in enumerate(self.available_lobbies):
                lobby_rect = pygame.Rect(200, 150 + i * 70, 600, 60)
                
                # Determine lobby status and colors
                status = lobby.get("status", "waiting")
                is_joinable = status in ["waiting"] and lobby['player_count'] < lobby['max_players']
                
                # Lobby background with different colors based on status
                if status == "in_game":
                    color = (100, 50, 50)  # Dark red for active games
                elif status == "full":
                    color = (50, 50, 100)  # Dark blue for full lobbies
                elif i % 2 == 0:
                    color = COLORS["DARK_GRAY"]
                else:
                    color = COLORS["GRAY"]
                    
                pygame.draw.rect(screen, color, lobby_rect)
                border_color = COLORS["GREEN"] if is_joinable else COLORS["WHITE"]
                pygame.draw.rect(screen, border_color, lobby_rect, 2)

                # Lobby ID (more characters for better identification)
                lobby_id_short = lobby['lobby_id'][:12] + "..." if len(lobby['lobby_id']) > 15 else lobby['lobby_id']
                lobby_id_text = self.small_font.render(lobby_id_short, True, COLORS["WHITE"])
                screen.blit(lobby_id_text, (lobby_rect.x + 20, lobby_rect.y + 10))

                # Player count
                player_count_text = f"{lobby['player_count']}/{lobby['max_players']}"
                player_text = self.small_font.render(player_count_text, True, COLORS["WHITE"])
                screen.blit(player_text, (lobby_rect.x + 300, lobby_rect.y + 10))

                # Status with appropriate colors
                status_text_map = {
                    "waiting": "Waiting",
                    "full": "Full", 
                    "in_game": "In Game"
                }
                status_color_map = {
                    "waiting": COLORS["GREEN"],
                    "full": COLORS["YELLOW"],
                    "in_game": COLORS["RED"]
                }
                
                status_display = status_text_map.get(status, status)
                status_color = status_color_map.get(status, COLORS["WHITE"])
                status_text = self.small_font.render(status_display, True, status_color)
                screen.blit(status_text, (lobby_rect.x + 400, lobby_rect.y + 10))

                # Action text
                if is_joinable:
                    action_text = self.small_font.render("Click to join", True, COLORS["CYAN"])
                    screen.blit(action_text, (lobby_rect.x + 20, lobby_rect.y + 35))
                elif status == "in_game":
                    action_text = self.small_font.render("Game in progress", True, COLORS["YELLOW"])
                    screen.blit(action_text, (lobby_rect.x + 20, lobby_rect.y + 35))
                elif status == "full":
                    action_text = self.small_font.render("Lobby full", True, COLORS["YELLOW"])
                    screen.blit(action_text, (lobby_rect.x + 20, lobby_rect.y + 35))

        # Back button
        pygame.draw.rect(screen, COLORS["RED"], self.buttons["back"])
        pygame.draw.rect(screen, COLORS["WHITE"], self.buttons["back"], 2)
        back_text = self.small_font.render("Back", True, COLORS["WHITE"])
        back_text_rect = back_text.get_rect(center=self.buttons["back"].center)
        screen.blit(back_text, back_text_rect)

    def _render_connection_failed(self, screen: pygame.Surface):
        text = self.font.render("Failed to connect to server", True, COLORS["RED"])
        text_rect = text.get_rect(
            center=(screen.get_width() // 2, screen.get_height() // 2)
        )
        screen.blit(text, text_rect)

    def get_next_scene(self):
        if self.next_scene:
            next_scene = self.next_scene
            self.next_scene = None
            return next_scene
        return None

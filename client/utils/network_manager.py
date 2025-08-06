import asyncio
import websockets
import json
import uuid
import logging
from typing import Optional, Callable, Dict, Any

logger = logging.getLogger(__name__)


class NetworkManager:
    def __init__(self, server_url: str = "ws://localhost:8000"):
        self.server_url = server_url
        self.websocket: Optional[websockets.WebSocketServerProtocol] = None
        self.player_id = str(uuid.uuid4())
        self.message_handlers: Dict[str, Callable] = {}
        self.connected = False
        logger.info(f"NetworkManager initialized with player_id: {self.player_id}")

    async def connect(self) -> bool:
        try:
            full_url = f"{self.server_url}/ws/{self.player_id}"
            logger.info(f"Attempting to connect to: {full_url}")
            self.websocket = await websockets.connect(full_url)
            self.connected = True
            logger.info("WebSocket connection established successfully")
            asyncio.create_task(self._listen_for_messages())
            return True
        except Exception as e:
            logger.error(f"Failed to connect to server: {e}")
            return False

    def is_connected(self) -> bool:
        return self.connected and self.websocket is not None

    async def disconnect(self):
        if self.websocket and self.connected:
            logger.info("Disconnecting from server")
            await self.websocket.close()
            self.connected = False
            logger.info("Disconnected successfully")

    async def send_message(self, message: Dict[str, Any]):
        if self.websocket and self.connected:
            try:
                logger.debug(f"Sending message: {message.get('type', 'unknown')}")
                await self.websocket.send(json.dumps(message))
                logger.debug("Message sent successfully")
            except Exception as e:
                logger.error(f"Failed to send message: {e}")
                self.connected = False
        else:
            logger.warning("Attempted to send message when not connected")

    async def _listen_for_messages(self):
        logger.info("Starting message listener")
        try:
            async for message in self.websocket:
                # logger.debug(f"Received raw message: {message}")
                data = json.loads(message)
                message_type = data.get("type")
                logger.debug(f"Processed message type: {message_type}")

                if message_type in self.message_handlers:
                    logger.debug(f"Calling handler for {message_type}")
                    self.message_handlers[message_type](data)
                else:
                    logger.warning(
                        f"No handler registered for message type: {message_type}"
                    )
        except Exception as e:
            logger.error(f"Connection lost: {e}")
            self.connected = False

    def register_handler(self, message_type: str, handler: Callable):
        logger.info(f"Registering handler for message type: {message_type}")
        self.message_handlers[message_type] = handler

    async def create_lobby(self, player_name: str):
        logger.info(f"Creating lobby for player: {player_name}")
        await self.send_message({"type": "create_lobby", "player_name": player_name})

    async def join_lobby(self, lobby_id: str, player_name: str):
        logger.info(f"Joining lobby {lobby_id} as {player_name}")
        await self.send_message(
            {"type": "join_lobby", "lobby_id": lobby_id, "player_name": player_name}
        )

    async def select_hero(self, hero_type: str):
        logger.info(f"Selecting hero type: {hero_type}")
        await self.send_message({"type": "select_hero", "hero_type": hero_type})

    async def start_game(self):
        logger.info("Requesting to start game")
        await self.send_message({"type": "start_game"})

    async def send_game_action(self, action: Dict[str, Any]):
        logger.debug(f"Sending game action: {action.get('type', 'unknown')}")
        await self.send_message({"type": "game_action", "action": action})

    async def list_lobbies(self):
        logger.info("Requesting lobby list")
        await self.send_message({"type": "list_lobbies"})

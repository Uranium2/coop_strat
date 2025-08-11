import asyncio
import json
import logging
import uuid
from typing import Dict

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from server.services.game_manager import GameManager
from server.services.lobby_manager import LobbyManager

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("server.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Co-op RTS Server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

lobby_manager = LobbyManager()
game_managers: Dict[str, GameManager] = {}

logger.info("Server starting up...")
logger.info("Lobby manager initialized")


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.player_lobbies: Dict[str, str] = {}

    async def connect(self, websocket: WebSocket, player_id: str):
        logger.info(f"Player {player_id} attempting to connect")
        await websocket.accept()
        self.active_connections[player_id] = websocket
        logger.info(
            f"Player {player_id} connected successfully. Total connections: {len(self.active_connections)}"
        )

    def disconnect(self, player_id: str):
        logger.info(f"Player {player_id} disconnecting")
        if player_id in self.active_connections:
            del self.active_connections[player_id]
            logger.info(f"Removed connection for {player_id}")
        if player_id in self.player_lobbies:
            lobby_id = self.player_lobbies[player_id]
            del self.player_lobbies[player_id]
            logger.info(f"Player {player_id} removed from lobby {lobby_id}")
            return lobby_id
        return None

    async def send_to_player(self, player_id: str, message: dict):
        if player_id in self.active_connections:
            try:
                logger.debug(
                    f"Sending message to {player_id}: {message.get('type', 'unknown')}"
                )
                await self.active_connections[player_id].send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Failed to send message to {player_id}: {e}")
                # Remove disconnected connection
                if player_id in self.active_connections:
                    del self.active_connections[player_id]
                    logger.info(f"Removed dead connection for {player_id}")
        else:
            logger.warning(
                f"Attempted to send message to disconnected player {player_id}"
            )

    async def send_to_lobby(self, lobby_id: str, message: dict):
        logger.debug(
            f"Sending message to lobby {lobby_id}: {message.get('type', 'unknown')}"
        )
        lobby = lobby_manager.get_lobby(lobby_id)
        if lobby:
            for player_id in lobby.players:
                await self.send_to_player(player_id, message)
        else:
            logger.warning(
                f"Attempted to send message to non-existent lobby {lobby_id}"
            )


manager = ConnectionManager()


@app.websocket("/ws/{player_id}")
async def websocket_endpoint(websocket: WebSocket, player_id: str):
    logger.info(f"WebSocket connection attempt from player {player_id}")
    await manager.connect(websocket, player_id)

    try:
        while True:
            data = await websocket.receive_text()
            logger.debug(f"Received message from {player_id}: {data}")
            message = json.loads(data)
            await handle_message(player_id, message)

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for player {player_id}")
        lobby_id = manager.disconnect(player_id)
        if lobby_id:
            lobby_manager.remove_player(lobby_id, player_id)
            await manager.send_to_lobby(
                lobby_id, {"type": "player_disconnected", "player_id": player_id}
            )
    except Exception as e:
        logger.error(f"Error in websocket for player {player_id}: {e}", exc_info=True)
        manager.disconnect(player_id)


async def handle_message(player_id: str, message: dict):
    message_type = message.get("type")
    logger.info(f"Handling message from {player_id}: {message_type}")

    if message_type == "create_lobby":
        logger.info(f"Player {player_id} creating lobby")
        lobby_id = str(uuid.uuid4())
        player_name = message.get("player_name", "Player")
        logger.debug(f"Generated lobby ID: {lobby_id}, player name: {player_name}")

        lobby = lobby_manager.create_lobby(lobby_id)
        success = lobby_manager.add_player(lobby_id, player_id, player_name)

        if success:
            manager.player_lobbies[player_id] = lobby_id
            logger.info(
                f"Lobby {lobby_id} created successfully with player {player_id}"
            )

            await manager.send_to_player(
                player_id,
                {
                    "type": "lobby_created",
                    "lobby_id": lobby_id,
                    "players": list(lobby.players.keys()),
                },
            )
        else:
            logger.error(f"Failed to add player {player_id} to lobby {lobby_id}")

    elif message_type == "join_lobby":
        lobby_id = message.get("lobby_id")
        player_name = message.get("player_name", "Player")
        logger.info(f"Player {player_id} attempting to join lobby {lobby_id}")

        # Check if player is already in this lobby
        current_lobby = manager.player_lobbies.get(player_id)
        if current_lobby == lobby_id:
            logger.info(f"Player {player_id} is already in lobby {lobby_id}")
            lobby = lobby_manager.get_lobby(lobby_id)
            if lobby:
                await manager.send_to_player(
                    player_id,
                    {
                        "type": "player_joined",
                        "player_id": player_id,
                        "player_name": player_name,
                        "players": list(lobby.players.keys()),
                    },
                )
            return

        # Remove player from previous lobby if any
        if current_lobby:
            logger.info(
                f"Removing player {player_id} from previous lobby {current_lobby}"
            )
            lobby_manager.remove_player(current_lobby, player_id)
            await manager.send_to_lobby(
                current_lobby, {"type": "player_disconnected", "player_id": player_id}
            )

        if lobby_manager.add_player(lobby_id, player_id, player_name):
            manager.player_lobbies[player_id] = lobby_id
            lobby = lobby_manager.get_lobby(lobby_id)
            logger.info(f"Player {player_id} joined lobby {lobby_id} successfully")

            await manager.send_to_lobby(
                lobby_id,
                {
                    "type": "player_joined",
                    "player_id": player_id,
                    "player_name": player_name,
                    "players": list(lobby.players.keys()),
                },
            )
        else:
            logger.warning(f"Player {player_id} failed to join lobby {lobby_id}")
            await manager.send_to_player(
                player_id, {"type": "join_failed", "reason": "Lobby not found or full"}
            )

    elif message_type == "select_hero":
        lobby_id = manager.player_lobbies.get(player_id)
        hero_type = message.get("hero_type")
        logger.info(
            f"Player {player_id} selecting hero {hero_type} in lobby {lobby_id}"
        )

        if lobby_id:
            lobby_manager.set_player_hero(lobby_id, player_id, hero_type)

            await manager.send_to_lobby(
                lobby_id,
                {
                    "type": "hero_selected",
                    "player_id": player_id,
                    "hero_type": hero_type,
                },
            )
        else:
            logger.warning(f"Player {player_id} not in any lobby when selecting hero")

    elif message_type == "start_game":
        lobby_id = manager.player_lobbies.get(player_id)
        logger.info(f"Player {player_id} requesting to start game in lobby {lobby_id}")

        if lobby_id:
            lobby = lobby_manager.get_lobby(lobby_id)
            if lobby and lobby.can_start_game():
                logger.info(f"Starting game for lobby {lobby_id}")
                try:
                    lobby.start_game()  # Mark lobby as active
                    game_manager = GameManager(lobby_id, lobby.players)
                    game_managers[lobby_id] = game_manager
                    initial_state = game_manager.get_game_state()

                    logger.info("Game state created successfully, serializing...")
                    game_state_dict = initial_state.dict()
                    logger.info("Game state serialized successfully")

                    await manager.send_to_lobby(
                        lobby_id,
                        {"type": "game_started", "game_state": game_state_dict},
                    )

                    asyncio.create_task(game_loop(lobby_id, game_manager))
                    logger.info(f"Game started successfully for lobby {lobby_id}")
                except Exception as e:
                    logger.error(
                        f"Failed to start game for lobby {lobby_id}: {e}", exc_info=True
                    )
            else:
                logger.warning(
                    f"Cannot start game for lobby {lobby_id} - conditions not met"
                )
        else:
            logger.warning(
                f"Player {player_id} not in any lobby when trying to start game"
            )

    elif message_type == "game_action":
        lobby_id = manager.player_lobbies.get(player_id)
        if lobby_id:
            action = message.get("action")
            logger.debug(
                f"Game action from {player_id} in lobby {lobby_id}: {action.get('type', 'unknown')}"
            )
            await handle_game_action(lobby_id, player_id, action)
        else:
            logger.warning(f"Player {player_id} sent game action but not in any lobby")

    elif message_type == "list_lobbies":
        logger.info(f"Player {player_id} requesting lobby list")
        lobbies = lobby_manager.list_active_lobbies()
        await manager.send_to_player(
            player_id, {"type": "lobby_list", "lobbies": lobbies}
        )

    elif message_type == "create_ping":
        lobby_id = manager.player_lobbies.get(player_id)
        if lobby_id:
            ping_id = message.get("ping_id")
            position_data = message.get("position")
            ping_type = message.get("ping_type")
            timestamp = message.get("timestamp")

            logger.debug(f"Creating ping from {player_id} at {position_data}")

            # Get player name
            lobby = lobby_manager.get_lobby(lobby_id)
            player_name = "Unknown"
            if lobby and player_id in lobby.players:
                player_name = lobby.players[player_id].name

            # Add ping to game state
            game_manager = game_managers.get(lobby_id)
            if game_manager:
                from shared.models.game_models import Ping, PingType, Position

                ping = Ping(
                    id=ping_id,
                    player_id=player_id,
                    player_name=player_name,
                    position=Position(x=position_data["x"], y=position_data["y"]),
                    ping_type=PingType(ping_type),
                    timestamp=timestamp,
                    duration=5.0,
                )

                game_manager.game_state.pings[ping_id] = ping

                # Broadcast ping to all players in lobby
                await manager.send_to_lobby(
                    lobby_id, {"type": "ping_created", "ping": ping.dict()}
                )
        else:
            logger.warning(
                f"Player {player_id} tried to create ping but not in any lobby"
            )

    else:
        logger.warning(f"Unknown message type from {player_id}: {message_type}")


async def handle_game_action(lobby_id: str, player_id: str, action: dict):
    game_manager = game_managers.get(lobby_id)
    if not game_manager:
        logger.warning(f"No game manager found for lobby {lobby_id}")
        return

    action_type = action.get("type")
    logger.debug(f"Processing game action {action_type} from {player_id}")

    if action_type == "move_hero":
        target_pos = action.get("target_position")
        from shared.models.game_models import Position

        position = Position(x=target_pos["x"], y=target_pos["y"])

        if game_manager.move_hero(player_id, position):
            logger.debug(f"Hero moved successfully for {player_id}")
            updated_state = game_manager.get_game_state()
            await manager.send_to_lobby(
                lobby_id, {"type": "game_update", "game_state": updated_state.dict()}
            )
        else:
            logger.warning(f"Failed to move hero for {player_id}")

    elif action_type == "move_to_target":
        target_type = action.get("target_type")
        target_id = action.get("target_id")
        target_position = action.get("target_position")

        from shared.models.game_models import Position, TargetType

        # Convert target position if provided
        pos = None
        if target_position:
            pos = Position(x=target_position["x"], y=target_position["y"])

        if game_manager.move_hero_to_target(
            player_id, TargetType(target_type), target_id, pos
        ):
            logger.debug(f"Hero targeting {target_type} for {player_id}")
            updated_state = game_manager.get_game_state()
            await manager.send_to_lobby(
                lobby_id, {"type": "game_update", "game_state": updated_state.dict()}
            )
        else:
            logger.warning(f"Failed to target {target_type} for {player_id}")

    elif action_type == "build":
        building_type = action.get("building_type")
        position_data = action.get("position")
        from shared.models.game_models import BuildingType, Position

        position = Position(x=position_data["x"], y=position_data["y"])

        if game_manager.build_structure(
            player_id, BuildingType(building_type), position
        ):
            logger.debug(
                f"Building {building_type} placed successfully for {player_id}"
            )
            updated_state = game_manager.get_game_state()
            await manager.send_to_lobby(
                lobby_id, {"type": "game_update", "game_state": updated_state.dict()}
            )
        else:
            logger.warning(f"Failed to build {building_type} for {player_id}")

    elif action_type == "toggle_pause":
        if game_manager.toggle_pause():
            logger.debug(f"Game pause toggled by {player_id}")
            updated_state = game_manager.get_game_state()
            await manager.send_to_lobby(
                lobby_id, {"type": "game_update", "game_state": updated_state.dict()}
            )
        else:
            logger.warning(f"Failed to toggle pause for {player_id}")

    else:
        logger.warning(f"Unknown game action type: {action_type}")


async def game_loop(lobby_id: str, game_manager: GameManager):
    logger.info(f"Starting game loop for lobby {lobby_id}")

    try:
        while game_manager.game_state.is_active:
            # Check if lobby still exists
            lobby = lobby_manager.get_lobby(lobby_id)
            if not lobby:
                logger.info(f"Lobby {lobby_id} no longer exists, stopping game loop")
                break

            # Check if lobby has any players
            if len(lobby.players) == 0:
                logger.info(f"Lobby {lobby_id} has no players, stopping game loop")
                game_manager.game_state.is_active = False
                break

            # Run at 60 FPS server tick rate
            await asyncio.sleep(1 / 60)

            # Update game logic - only sends network updates when needed
            game_state = game_manager.update()
            if game_state:
                await manager.send_to_lobby(
                    lobby_id, {"type": "game_update", "game_state": game_state.dict()}
                )
    except Exception as e:
        logger.error(f"Error in game loop for lobby {lobby_id}: {e}", exc_info=True)
    finally:
        logger.info(f"Game ended for lobby {lobby_id}")

        # Reset lobby state so it can start a new game
        lobby = lobby_manager.get_lobby(lobby_id)
        if lobby:
            logger.info(f"Resetting lobby {lobby_id} to allow new games")
            lobby.is_game_active = False
            lobby.save()

        if lobby_id in game_managers:
            del game_managers[lobby_id]


@app.get("/")
async def root():
    logger.info("Health check endpoint accessed")
    return {"message": "Co-op RTS Server is running"}


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "active_connections": len(manager.active_connections),
        "active_lobbies": len(lobby_manager.lobbies),
        "active_games": len(game_managers),
    }


@app.get("/api/lobbies")
async def get_lobbies():
    """REST API endpoint to check lobby status"""
    import time

    current_time = time.time()
    all_lobbies = []
    for lobby_id in lobby_manager.db_manager.list_lobbies():
        lobby = lobby_manager.get_lobby(lobby_id)
        if lobby:
            age_minutes = (current_time - lobby.created_at) / 60
            inactive_minutes = (current_time - lobby.last_activity) / 60
            all_lobbies.append(
                {
                    "lobby_id": lobby_id,
                    "player_count": len(lobby.players),
                    "max_players": lobby.max_players,
                    "is_game_active": lobby.is_game_active,
                    "players": list(lobby.players.keys()),
                    "age_minutes": round(age_minutes, 1),
                    "inactive_minutes": round(inactive_minutes, 1),
                }
            )

    available_lobbies = lobby_manager.list_active_lobbies()

    return {
        "all_lobbies": all_lobbies,
        "available_lobbies": available_lobbies,
        "total_lobbies": len(all_lobbies),
        "available_count": len(available_lobbies),
        "timestamp": current_time,
    }


if __name__ == "__main__":
    import uvicorn

    logger.info("Starting server with uvicorn on port 8000")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")

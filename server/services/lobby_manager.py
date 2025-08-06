import redis
import json
import logging
import time
from typing import Dict, Optional, List
from shared.models.game_models import Player, HeroType, Resources

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, redis_host: str = "localhost", redis_port: int = 6379):
        try:
            self.redis_client = redis.Redis(
                host=redis_host, 
                port=redis_port, 
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            # Test connection
            self.redis_client.ping()
            logger.info(f"Connected to Redis at {redis_host}:{redis_port}")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}. Using in-memory storage.")
            self.redis_client = None
    
    def save_lobby(self, lobby_id: str, lobby_data: dict):
        """Save lobby data to database"""
        if self.redis_client:
            try:
                key = f"lobby:{lobby_id}"
                self.redis_client.setex(key, 3600, json.dumps(lobby_data))  # 1 hour expiry
                logger.debug(f"Saved lobby {lobby_id} to Redis")
            except Exception as e:
                logger.error(f"Failed to save lobby to Redis: {e}")
    
    def load_lobby(self, lobby_id: str) -> Optional[dict]:
        """Load lobby data from database"""
        if self.redis_client:
            try:
                key = f"lobby:{lobby_id}"
                data = self.redis_client.get(key)
                if data:
                    logger.debug(f"Loaded lobby {lobby_id} from Redis")
                    return json.loads(data)
            except Exception as e:
                logger.error(f"Failed to load lobby from Redis: {e}")
        return None
    
    def delete_lobby(self, lobby_id: str):
        """Delete lobby from database"""
        if self.redis_client:
            try:
                key = f"lobby:{lobby_id}"
                self.redis_client.delete(key)
                logger.debug(f"Deleted lobby {lobby_id} from Redis")
            except Exception as e:
                logger.error(f"Failed to delete lobby from Redis: {e}")
    
    def list_lobbies(self) -> List[str]:
        """Get list of all active lobby IDs"""
        if self.redis_client:
            try:
                keys = self.redis_client.keys("lobby:*")
                lobby_ids = [key.replace("lobby:", "") for key in keys]
                logger.debug(f"Found {len(lobby_ids)} lobbies in Redis")
                return lobby_ids
            except Exception as e:
                logger.error(f"Failed to list lobbies from Redis: {e}")
        return []

class Lobby:
    def __init__(self, lobby_id: str, db_manager: DatabaseManager):
        self.lobby_id = lobby_id
        self.players: Dict[str, Player] = {}
        self.max_players = 4
        self.is_game_active = False
        self.created_at = time.time()
        self.last_activity = time.time()
        self.db_manager = db_manager
        logger.info(f"Created lobby {lobby_id}")
    
    def to_dict(self) -> dict:
        """Serialize lobby to dictionary"""
        return {
            "lobby_id": self.lobby_id,
            "players": {pid: {
                "id": p.id,
                "name": p.name,
                "hero_type": p.hero_type.value,
                "resources": p.resources.dict(),
                "is_connected": p.is_connected
            } for pid, p in self.players.items()},
            "max_players": self.max_players,
            "is_game_active": self.is_game_active,
            "created_at": self.created_at,
            "last_activity": self.last_activity
        }
    
    @classmethod
    def from_dict(cls, data: dict, db_manager: DatabaseManager) -> 'Lobby':
        """Deserialize lobby from dictionary"""
        lobby = cls(data["lobby_id"], db_manager)
        lobby.max_players = data["max_players"]
        lobby.is_game_active = data["is_game_active"]
        lobby.created_at = data.get("created_at", time.time())
        lobby.last_activity = data.get("last_activity", time.time())
        
        for pid, pdata in data["players"].items():
            lobby.players[pid] = Player(
                id=pdata["id"],
                name=pdata["name"],
                hero_type=HeroType(pdata["hero_type"]),
                resources=Resources(**pdata["resources"]),
                is_connected=pdata["is_connected"]
            )
        
        return lobby
    
    def save(self):
        """Save lobby to database"""
        self.db_manager.save_lobby(self.lobby_id, self.to_dict())
    
    def add_player(self, player_id: str, player_name: str) -> bool:
        if self.is_game_active:
            logger.warning(f"Cannot add player {player_id} to lobby {self.lobby_id} - game is active")
            return False
            
        if len(self.players) >= self.max_players:
            logger.warning(f"Cannot add player {player_id} to lobby {self.lobby_id} - lobby full")
            return False
        
        if player_id in self.players:
            logger.info(f"Player {player_id} is already in lobby {self.lobby_id}")
            return True  # Already in lobby, consider it success
        
        self.players[player_id] = Player(
            id=player_id,
            name=player_name,
            hero_type=HeroType.TANK,
            resources=Resources(wood=100, stone=50, wheat=50, metal=10, gold=5)
        )
        self.last_activity = time.time()
        logger.info(f"Added player {player_id} ({player_name}) to lobby {self.lobby_id} - now {len(self.players)}/{self.max_players} players")
        self.save()
        return True
    
    def remove_player(self, player_id: str):
        if player_id in self.players:
            logger.info(f"Removing player {player_id} from lobby {self.lobby_id}")
            del self.players[player_id]
            self.last_activity = time.time()
            self.save()
    
    def set_player_hero(self, player_id: str, hero_type: HeroType):
        if player_id in self.players:
            logger.info(f"Player {player_id} set hero type to {hero_type}")
            self.players[player_id].hero_type = hero_type
            self.save()
    
    def can_start_game(self) -> bool:
        # Check if at least one player has selected a hero
        players_with_heroes = sum(1 for player in self.players.values() if player.hero_type)
        can_start = len(self.players) >= 1 and not self.is_game_active and players_with_heroes >= 1
        logger.info(f"Lobby {self.lobby_id} can start game: {can_start} (players: {len(self.players)}, active: {self.is_game_active}, heroes: {players_with_heroes})")
        return can_start
    
    def start_game(self):
        logger.info(f"Starting game for lobby {self.lobby_id}")
        self.is_game_active = True
        self.save()

class LobbyManager:
    def __init__(self):
        self.lobbies: Dict[str, Lobby] = {}
        self.db_manager = DatabaseManager()
        logger.info("LobbyManager initialized with database support")
        
        # Load existing lobbies from database
        self._load_existing_lobbies()
    
    def _load_existing_lobbies(self):
        """Load existing lobbies from database on startup"""
        lobby_ids = self.db_manager.list_lobbies()
        for lobby_id in lobby_ids:
            try:
                lobby_data = self.db_manager.load_lobby(lobby_id)
                if lobby_data:
                    lobby = Lobby.from_dict(lobby_data, self.db_manager)
                    self.lobbies[lobby_id] = lobby
                    logger.info(f"Restored lobby {lobby_id} from database")
            except Exception as e:
                logger.error(f"Failed to restore lobby {lobby_id}: {e}")
    
    def create_lobby(self, lobby_id: str) -> Lobby:
        logger.info(f"Creating lobby with ID: {lobby_id}")
        lobby = Lobby(lobby_id, self.db_manager)
        self.lobbies[lobby_id] = lobby
        lobby.save()
        logger.info(f"Lobby {lobby_id} created successfully. Total lobbies: {len(self.lobbies)}")
        return lobby
    
    def get_lobby(self, lobby_id: str) -> Optional[Lobby]:
        # First check in-memory cache
        if lobby_id in self.lobbies:
            # logger.debug(f"Found lobby {lobby_id} in memory")
            return self.lobbies[lobby_id]
        
        # Try loading from database
        lobby_data = self.db_manager.load_lobby(lobby_id)
        if lobby_data:
            try:
                lobby = Lobby.from_dict(lobby_data, self.db_manager)
                self.lobbies[lobby_id] = lobby
                logger.info(f"Loaded lobby {lobby_id} from database")
                return lobby
            except Exception as e:
                logger.error(f"Failed to deserialize lobby {lobby_id}: {e}")
        
        logger.warning(f"Lobby {lobby_id} not found")
        return None
    
    def add_player(self, lobby_id: str, player_id: str, player_name: str) -> bool:
        logger.info(f"Adding player {player_id} to lobby {lobby_id}")
        lobby = self.get_lobby(lobby_id)
        if lobby:
            return lobby.add_player(player_id, player_name)
        logger.error(f"Cannot add player to non-existent lobby {lobby_id}")
        return False
    
    def remove_player(self, lobby_id: str, player_id: str):
        logger.info(f"Removing player {player_id} from lobby {lobby_id}")
        lobby = self.get_lobby(lobby_id)
        if lobby:
            lobby.remove_player(player_id)
            if len(lobby.players) == 0:
                if lobby.is_game_active:
                    # If game was active but no players remain, reset the lobby to waiting state
                    logger.info(f"Lobby {lobby_id} is empty after game was active, resetting to waiting state")
                    lobby.is_game_active = False
                    lobby.save()
                else:
                    # Keep empty waiting lobbies for a grace period for reconnection
                    logger.info(f"Lobby {lobby_id} is empty (waiting state), keeping for potential rejoin")
                    lobby.save()
    
    def set_player_hero(self, lobby_id: str, player_id: str, hero_type: str):
        lobby = self.get_lobby(lobby_id)
        if lobby:
            lobby.set_player_hero(player_id, HeroType(hero_type))
    
    def list_active_lobbies(self) -> List[dict]:
        """Get list of all lobbies with their status"""
        lobbies = []
        current_time = time.time()
        
        # Check both database and in-memory lobbies
        all_lobby_ids = set(self.db_manager.list_lobbies())
        all_lobby_ids.update(self.lobbies.keys())
        
        logger.info(f"Total lobbies to check: {len(all_lobby_ids)} (DB: {len(self.db_manager.list_lobbies())}, Memory: {len(self.lobbies)})")
        logger.info(f"DB lobbies: {self.db_manager.list_lobbies()}")
        logger.info(f"Memory lobbies: {list(self.lobbies.keys())}")
        
        for lobby_id in all_lobby_ids:
            lobby = self.get_lobby(lobby_id)
            if lobby:
                age_minutes = (current_time - lobby.last_activity) / 60
                logger.info(f"Processing lobby {lobby_id}: players={len(lobby.players)}, is_game_active={lobby.is_game_active}, age={age_minutes:.1f}min")
                
                # Clean up very old empty lobbies (older than 15 minutes)
                if len(lobby.players) == 0 and (current_time - lobby.last_activity) > 900:  # 15 minutes
                    logger.info(f"Cleaning up old empty lobby {lobby_id} (age: {age_minutes:.1f} minutes)")
                    self.db_manager.delete_lobby(lobby_id)
                    if lobby_id in self.lobbies:
                        del self.lobbies[lobby_id]
                    continue
                
                # Include ALL lobbies but with status information
                status = "in_game" if lobby.is_game_active else "waiting"
                if len(lobby.players) >= lobby.max_players and not lobby.is_game_active:
                    status = "full"
                
                lobby_info = {
                    "lobby_id": lobby_id,
                    "player_count": len(lobby.players),
                    "max_players": lobby.max_players,
                    "status": status,
                    "is_game_active": lobby.is_game_active
                }
                lobbies.append(lobby_info)
                logger.info(f"✓ Added lobby {lobby_id} to list: {lobby_info}")
            else:
                logger.warning(f"Could not load lobby {lobby_id} from database or memory")
        
        logger.info(f"Final result: Returning {len(lobbies)} lobbies: {[l['lobby_id'][:8] + '...' for l in lobbies]}")
        return lobbies
from enum import Enum
from typing import Dict, List, Optional, Tuple
from pydantic import BaseModel

class HeroType(str, Enum):
    TANK = "TANK"
    BUILDER = "BUILDER" 
    ARCHER = "ARCHER"
    MAGE = "MAGE"

class ResourceType(str, Enum):
    WOOD = "wood"
    STONE = "stone"
    WHEAT = "wheat"
    METAL = "metal"
    GOLD = "gold"

class BuildingType(str, Enum):
    TOWN_HALL = "TOWN_HALL"
    WALL = "WALL"
    TOWER = "TOWER"
    FARM = "FARM"
    MINE = "MINE"
    WOOD_CUTTER = "WOOD_CUTTER"
    GOLD_MINE = "GOLD_MINE"
    BARRACKS = "BARRACKS"
    ARCHERY_RANGE = "ARCHERY_RANGE"
    CANNON_FOUNDRY = "CANNON_FOUNDRY"

class UnitType(str, Enum):
    SOLDIER = "SOLDIER"
    ARCHER = "ARCHER"
    CANNON = "CANNON"

class TileType(str, Enum):
    EMPTY = "EMPTY"
    WOOD = "WOOD"
    STONE = "STONE"
    WHEAT = "WHEAT"
    METAL = "METAL"
    GOLD = "GOLD"
    WALL = "WALL"

class Position(BaseModel):
    x: float
    y: float

class Resources(BaseModel):
    wood: int = 0
    stone: int = 0
    wheat: int = 0
    metal: int = 0
    gold: int = 0

class Hero(BaseModel):
    id: str
    player_id: str
    hero_type: HeroType
    position: Position
    health: int
    max_health: int

class Building(BaseModel):
    id: str
    building_type: BuildingType
    position: Position
    health: int
    max_health: int
    player_id: str
    size: Tuple[int, int]

class Unit(BaseModel):
    id: str
    unit_type: UnitType
    position: Position
    health: int
    max_health: int
    player_id: str
    target_position: Optional[Position] = None

class Enemy(BaseModel):
    id: str
    position: Position
    health: int
    max_health: int
    target_position: Optional[Position] = None
    is_active: bool = False

class Player(BaseModel):
    id: str
    name: str
    hero_type: HeroType
    resources: Resources
    is_connected: bool = True

class GameState(BaseModel):
    lobby_id: str = ""
    players: Dict[str, Player]
    heroes: Dict[str, Hero]
    buildings: Dict[str, Building]
    units: Dict[str, Unit]
    enemies: Dict[str, Enemy]
    map_data: List[List[TileType]]
    fog_of_war: List[List[bool]]
    game_time: float
    is_active: bool = False

class MapTile(BaseModel):
    tile_type: TileType
    resource_amount: int = 0
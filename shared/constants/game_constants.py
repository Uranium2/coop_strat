SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080
FPS = 60

MAP_WIDTH = 200
MAP_HEIGHT = 200
TILE_SIZE = 32

HERO_TYPES = {
    "TANK": {"health": 200, "speed": 2, "build_speed": 0.8},
    "BUILDER": {"health": 100, "speed": 3, "build_speed": 2.0},
    "ARCHER": {"health": 80, "speed": 4, "build_speed": 0.5},
    "MAGE": {"health": 60, "speed": 3, "build_speed": 1.0},
}

BUILDING_TYPES = {
    "TOWN_HALL": {"health": 1000, "cost": {}, "size": (3, 3)},
    "WALL": {"health": 50, "cost": {"wood": 10}, "size": (1, 1)},
    "TOWER": {"health": 100, "cost": {"wood": 20, "stone": 15}, "size": (1, 1)},
    "FARM": {"health": 75, "cost": {"wood": 15}, "size": (2, 2)},
    "MINE": {"health": 100, "cost": {"wood": 25, "stone": 10}, "size": (2, 2)},
    "WOOD_CUTTER": {"health": 80, "cost": {"wood": 20}, "size": (2, 2)},
    "GOLD_MINE": {"health": 120, "cost": {"wood": 30, "stone": 20}, "size": (2, 2)},
    "BARRACKS": {"health": 150, "cost": {"wood": 40, "stone": 30}, "size": (3, 2)},
    "ARCHERY_RANGE": {"health": 120, "cost": {"wood": 35, "stone": 25}, "size": (3, 2)},
    "CANNON_FOUNDRY": {
        "health": 200,
        "cost": {"wood": 50, "stone": 40, "metal": 20},
        "size": (3, 3),
    },
}

RESOURCE_TYPES = ["wood", "stone", "wheat", "metal", "gold"]

UNIT_TYPES = {
    "SOLDIER": {"health": 60, "speed": 3, "cost": {"wheat": 2, "metal": 1}},
    "ARCHER": {"health": 40, "speed": 4, "cost": {"wheat": 1, "wood": 2}},
    "CANNON": {"health": 80, "speed": 2, "cost": {"wheat": 3, "metal": 3, "gold": 1}},
}

COLORS = {
    "BLACK": (0, 0, 0),
    "WHITE": (255, 255, 255),
    "RED": (255, 0, 0),
    "GREEN": (0, 255, 0),
    "BLUE": (0, 0, 255),
    "BROWN": (139, 69, 19),
    "GRAY": (128, 128, 128),
    "DARK_GRAY": (64, 64, 64),
    "YELLOW": (255, 255, 0),
    "DARK_GREEN": (0, 100, 0),
    "PURPLE": (128, 0, 128),
    "CYAN": (0, 255, 255),
}

FOG_COLOR = (50, 50, 50, 180)
VISION_RADIUS = 5

WAVE_SPAWN_INTERVAL = 120
ENEMY_SPAWN_CORNERS = [
    (0, 0),
    (MAP_WIDTH - 1, 0),
    (0, MAP_HEIGHT - 1),
    (MAP_WIDTH - 1, MAP_HEIGHT - 1),
]

RESOURCE_TICK_RATE = 2.0

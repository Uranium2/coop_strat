SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080
FPS = 60

MAP_WIDTH = 200
MAP_HEIGHT = 200
TILE_SIZE = 32

HERO_TYPES = {
    "TANK": {
        "health": 200,
        "speed": 2,
        "build_speed": 1.0,
        "attack_damage": 15,
        "attack_range": 1.5,  # Melee fighter - close combat
        "attack_speed": 0.8,
    },
    "BUILDER": {
        "health": 150,
        "speed": 4,
        "build_speed": 2.0,
        "attack_damage": 8,
        "attack_range": 1.2,  # Short range - focus on building, not combat
        "attack_speed": 1.0,
    },
    "ARCHER": {
        "health": 80,
        "speed": 4,
        "build_speed": 1.0,
        "attack_damage": 12,
        "attack_range": 6.0,  # Long range but not excessive for gameplay balance
        "attack_speed": 1.5,
    },
    "MAGE": {
        "health": 70,
        "speed": 3,
        "build_speed": 1.0,
        "attack_damage": 40,
        "attack_range": 4.0,  # Medium-long range magical attacks
        "attack_speed": 0.5,
    },
}

BUILDING_TYPES = {
    "TOWN_HALL": {
        "health": 1000,
        "cost": {},
        "size": (3, 3),
        "category": "SPECIAL",
        "construction_time": 0.0,
    },
    "WALL": {
        "health": 50,
        "cost": {"wood": 10},
        "size": (1, 1),
        "category": "SPECIAL",
        "construction_time": 5.0,
    },
    "TOWER": {
        "health": 100,
        "cost": {"wood": 20, "stone": 15},
        "size": (1, 1),
        "category": "DEFENSIVE",
        "construction_time": 15.0,
        "attack_damage": 25.0,
        "attack_range": 6.0,
        "attack_speed": 1.5,  # Attacks per second
    },
    "FARM": {
        "health": 75,
        "cost": {"wood": 15},
        "size": (2, 2),
        "category": "RESOURCE",
        "construction_time": 10.0,
        "resource_type": "wheat",
        "resource_per_tick": 5,
        "tick_interval": 30.0,
    },
    "MINE": {
        "health": 100,
        "cost": {"wood": 25, "stone": 10},
        "size": (2, 2),
        "category": "RESOURCE",
        "construction_time": 15.0,
        "resource_type": "stone",
        "resource_per_tick": 3,
        "tick_interval": 30.0,
    },
    "WOOD_CUTTER": {
        "health": 80,
        "cost": {"wood": 20},
        "size": (2, 2),
        "category": "RESOURCE",
        "construction_time": 12.0,
        "resource_type": "wood",
        "resource_per_tick": 4,
        "tick_interval": 30.0,
    },
    "GOLD_MINE": {
        "health": 120,
        "cost": {"wood": 30, "stone": 20},
        "size": (2, 2),
        "category": "RESOURCE",
        "construction_time": 20.0,
        "resource_type": "gold",
        "resource_per_tick": 2,
        "tick_interval": 30.0,
    },
    "BARRACKS": {
        "health": 150,
        "cost": {"wood": 40, "stone": 30},
        "size": (3, 2),
        "category": "UPGRADE",
        "construction_time": 25.0,
        "available_upgrades": ["melee_damage", "melee_armor", "unit_speed"],
    },
    "ARCHERY_RANGE": {
        "health": 120,
        "cost": {"wood": 35, "stone": 25},
        "size": (3, 2),
        "category": "UPGRADE",
        "construction_time": 20.0,
        "available_upgrades": ["ranged_damage", "ranged_range", "attack_speed"],
    },
    "CANNON_FOUNDRY": {
        "health": 200,
        "cost": {"wood": 50, "stone": 40, "metal": 20},
        "size": (3, 3),
        "category": "DEFENSIVE",
        "construction_time": 30.0,
        "attack_damage": 60.0,
        "attack_range": 8.0,
        "attack_speed": 0.5,  # Slow but powerful
    },
}

RESOURCE_TYPES = ["wood", "stone", "wheat", "metal", "gold"]

# Upgrade definitions
UPGRADES = {
    "melee_damage": {
        "name": "Melee Damage",
        "description": "Increases melee unit damage by 20%",
        "cost": {"gold": 50, "metal": 25},
        "effect": {"unit_damage_multiplier": 1.2},
        "applies_to": ["SOLDIER"],
    },
    "melee_armor": {
        "name": "Melee Armor",
        "description": "Increases melee unit health by 25%",
        "cost": {"gold": 40, "stone": 30},
        "effect": {"unit_health_multiplier": 1.25},
        "applies_to": ["SOLDIER"],
    },
    "unit_speed": {
        "name": "Unit Speed",
        "description": "Increases unit movement speed by 15%",
        "cost": {"gold": 30, "wheat": 20},
        "effect": {"unit_speed_multiplier": 1.15},
        "applies_to": ["SOLDIER", "ARCHER", "CANNON"],
    },
    "ranged_damage": {
        "name": "Ranged Damage",
        "description": "Increases ranged unit damage by 25%",
        "cost": {"gold": 60, "wood": 40},
        "effect": {"unit_damage_multiplier": 1.25},
        "applies_to": ["ARCHER"],
    },
    "ranged_range": {
        "name": "Ranged Range",
        "description": "Increases ranged unit attack range by 30%",
        "cost": {"gold": 45, "metal": 20},
        "effect": {"unit_range_multiplier": 1.3},
        "applies_to": ["ARCHER"],
    },
    "attack_speed": {
        "name": "Attack Speed",
        "description": "Increases unit attack speed by 20%",
        "cost": {"gold": 35, "wheat": 25},
        "effect": {"unit_attack_speed_multiplier": 1.2},
        "applies_to": ["ARCHER", "SOLDIER"],
    },
}

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
    "ORANGE": (255, 165, 0),
    "DARK_GREEN": (0, 100, 0),
    "PURPLE": (128, 0, 128),
    "CYAN": (0, 255, 255),
}

FOG_COLOR = (50, 50, 50, 180)
VISION_RADIUS = 5

# Combat constants
ARMOR_REDUCTION_FACTOR = 0.02
MAGIC_RESIST_FACTOR = 0.02
CRITICAL_CHANCE = 0.1
CRITICAL_MULTIPLIER = 1.5
DAMAGE_VARIANCE = 0.2

# Enemy types
ENEMY_TYPES = {
    "BASIC": {
        "health": 30,
        "speed": 4.0,  # Balanced speed - 35 seconds to reach town hall
        "attack_damage": 10,
        "armor": 0,
        "magic_resist": 0,
        "attack_range": 1.0,  # Melee enemy
        "attack_speed": 1.0,
    },
    "RANGED": {
        "health": 20,
        "speed": 3.0,  # Slower ranged unit
        "attack_damage": 8,
        "armor": 0,
        "magic_resist": 0,
        "attack_range": 3.5,  # Ranged enemy with moderate range
        "attack_speed": 1.2,
    },
    "HEAVY": {
        "health": 50,
        "speed": 2.5,  # Slow heavy unit
        "attack_damage": 15,
        "armor": 2,
        "magic_resist": 0,
        "attack_range": 1.2,  # Slightly longer melee range
        "attack_speed": 0.7,
    },
    "FAST": {
        "health": 15,
        "speed": 6.0,  # Fast unit
        "attack_damage": 6,
        "armor": 0,
        "magic_resist": 0,
        "attack_range": 0.8,  # Short range but fast
        "attack_speed": 1.5,
    },
}

WAVE_SPAWN_INTERVAL = 300  # 5 minutes (300 seconds) between waves
FIRST_WAVE_DELAY = 60  # 1 minute (60 seconds) before first wave
ENEMY_SPAWN_CORNERS = [
    (0, 0),
    (MAP_WIDTH - 1, 0),
    (0, MAP_HEIGHT - 1),
    (MAP_WIDTH - 1, MAP_HEIGHT - 1),
]

RESOURCE_TICK_RATE = 2.0

#!/usr/bin/env python3
"""Debug why enemies stop before reaching attack range"""

import asyncio
import logging
import time
from typing import Dict

from server.services.game_manager import GameManager
from shared.models.game_models import (
    BuildingType,
    Player,
    Resources,
)

# Configure logging for more details
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


async def debug_enemy_movement_stopping():
    """Debug why enemies stop before reaching attack range"""
    print("=== Debugging Enemy Movement Stopping ===")

    # Create a test player
    test_player = Player(
        id="player1",
        name="TestPlayer",
        hero_type="TANK",
        resources=Resources(wood=100, stone=100, food=100),
    )
    players: Dict[str, Player] = {"player1": test_player}

    # Create game manager
    game_manager = GameManager("test_lobby", players)

    # Get the town hall
    town_hall = None
    for building in game_manager.game_state.buildings.values():
        if building.building_type == BuildingType.TOWN_HALL:
            town_hall = building
            break

    print(
        f"Town hall center: ({town_hall.position.x + town_hall.size[0] / 2}, {town_hall.position.y + town_hall.size[1] / 2})"
    )

    # Spawn single enemy for easier debugging
    game_manager._spawn_enemy_wave()
    enemy = next(iter(game_manager.game_state.enemies.values()))

    # Remove other enemies to avoid collision issues
    enemies_to_remove = [
        e_id for e_id in game_manager.game_state.enemies.keys() if e_id != enemy.id
    ]
    for e_id in enemies_to_remove:
        del game_manager.game_state.enemies[e_id]

    print(f"Single enemy: {enemy.id}")
    print(f"Initial position: ({enemy.position.x:.2f}, {enemy.position.y:.2f})")

    # Position enemy close but outside attack range to see what happens
    enemy.position.x = 98.0  # About 4 units from town hall center
    enemy.position.y = 101.5
    enemy.speed = 2.0  # Slower for easier observation

    print(f"Positioned enemy at: ({enemy.position.x:.2f}, {enemy.position.y:.2f})")

    # Run updates and track movement
    for i in range(50):  # Extended from 20 to 50
        time.sleep(1.0 / game_manager.tick_rate + 0.001)

        old_pos = (enemy.position.x, enemy.position.y)
        game_manager.update()
        new_pos = (enemy.position.x, enemy.position.y)

        # Calculate distance to town hall center
        town_hall_center_x = town_hall.position.x + town_hall.size[0] / 2
        town_hall_center_y = town_hall.position.y + town_hall.size[1] / 2
        distance = (
            (enemy.position.x - town_hall_center_x) ** 2
            + (enemy.position.y - town_hall_center_y) ** 2
        ) ** 0.5

        # Check if enemy should be able to attack
        effective_range = enemy.attack_range + max(town_hall.size) / 2
        can_attack = distance <= effective_range

        print(
            f"Update {i + 1}: Pos=({new_pos[0]:.2f}, {new_pos[1]:.2f}), Distance={distance:.2f}, Can attack={can_attack}, Health={town_hall.health}"
        )

        if old_pos == new_pos and distance > effective_range:
            print(
                f"  ⚠️  Enemy stopped moving but is still {distance:.2f} units away (need {effective_range:.2f})"
            )
            break
        elif can_attack and town_hall.health < 1000:
            print("  ✅ Enemy successfully attacked town hall!")
            break


if __name__ == "__main__":
    asyncio.run(debug_enemy_movement_stopping())

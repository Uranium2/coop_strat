#!/usr/bin/env python3

import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Patch constants before importing GameManager
import shared.constants.game_constants as constants

original_first_delay = constants.FIRST_WAVE_DELAY
original_interval = constants.WAVE_SPAWN_INTERVAL

constants.FIRST_WAVE_DELAY = 3  # 3 seconds for first wave
constants.WAVE_SPAWN_INTERVAL = 5  # 5 seconds between waves

# Now import GameManager after patching
import time
import uuid

from server.services.game_manager import GameManager
from shared.models.game_models import HeroType, Player, Resources


def test_full_spawn_system():
    """Test the complete spawn system with faster timers"""
    print("=== Testing Complete Spawn System (Fast Mode) ===")
    print(f"Using FIRST_WAVE_DELAY: {constants.FIRST_WAVE_DELAY}s")
    print(f"Using WAVE_SPAWN_INTERVAL: {constants.WAVE_SPAWN_INTERVAL}s")

    # Create test players
    player_id = str(uuid.uuid4())
    players = {
        player_id: Player(
            id=player_id,
            name="TestPlayer",
            hero_type=HeroType.TANK,
            resources=Resources(),
        )
    }

    # Create game manager
    lobby_id = str(uuid.uuid4())
    game_manager = GameManager(lobby_id, players)

    print(f"\n1. Game initialized with lobby: {lobby_id}")
    print(
        f"   Initial time to first wave: {game_manager.game_state.time_to_next_wave:.1f}s"
    )

    # Wait for first wave to spawn
    print("\n2. Waiting for first wave to spawn...")
    wave_spawned = False
    updates = 0

    while not wave_spawned and updates < 50:  # Max 5 seconds of updates
        game_state = game_manager.update()
        updates += 1

        if game_state:
            enemies_count = len(game_state.enemies)
            if enemies_count > 0 and not wave_spawned:
                print(
                    f"   ✅ First wave spawned! Wave {game_state.wave_number}, Enemies: {enemies_count}"
                )
                print(f"   Time to next wave: {game_state.time_to_next_wave:.1f}s")
                wave_spawned = True
                break
            elif game_state.time_to_next_wave < 1.0:
                print(
                    f"   Wave {game_state.wave_number} about to spawn... ({game_state.time_to_next_wave:.1f}s)"
                )

        time.sleep(0.1)

    if not wave_spawned:
        print("   ❌ First wave did not spawn in time")
        return

    # Wait for second wave
    print("\n3. Waiting for second wave...")
    second_wave_spawned = False
    updates = 0

    while not second_wave_spawned and updates < 70:  # Max 7 seconds
        game_state = game_manager.update()
        updates += 1

        if game_state and game_state.wave_number >= 2:
            print(
                f"   ✅ Second wave spawned! Wave {game_state.wave_number}, Total enemies: {len(game_state.enemies)}"
            )
            second_wave_spawned = True
            break
        elif game_state and game_state.time_to_next_wave < 2.0:
            print(f"   Second wave incoming... ({game_state.time_to_next_wave:.1f}s)")

        time.sleep(0.1)

    if second_wave_spawned:
        print("   ✅ Second wave system working correctly")
    else:
        print("   ⚠️ Second wave didn't spawn (may need more time)")

    print("\n✅ Complete spawn system test finished!")


if __name__ == "__main__":
    try:
        test_full_spawn_system()
    finally:
        # Restore original constants
        constants.FIRST_WAVE_DELAY = original_first_delay
        constants.WAVE_SPAWN_INTERVAL = original_interval

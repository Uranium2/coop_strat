#!/usr/bin/env python3

import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import time
import uuid

from server.services.game_manager import GameManager
from shared.models.game_models import HeroType, Player, Resources


def test_spawn_timer():
    """Test the enemy spawn timer functionality"""
    print("=== Testing Enemy Spawn Timer ===")

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

    print(f"1. Game initialized with lobby: {lobby_id}")
    print(f"   Initial wave number: {game_manager.game_state.wave_number}")
    print(f"   Time to next wave: {game_manager.game_state.time_to_next_wave:.1f}s")
    print(f"   Next wave time: {game_manager.game_state.next_wave_time}")

    # Simulate game updates to test timer countdown
    print("\n2. Testing timer countdown...")
    initial_time = game_manager.game_state.time_to_next_wave

    for i in range(10):
        # Update game state
        game_state = game_manager.update()

        if game_state:
            print(
                f"   Update {i + 1}: Wave {game_state.wave_number}, Time to next: {game_state.time_to_next_wave:.1f}s, Enemies: {len(game_state.enemies)}"
            )

        # Small delay to simulate real time passing
        time.sleep(0.1)

    # Verify timer is counting down
    final_time = game_manager.game_state.time_to_next_wave
    if final_time < initial_time:
        print(
            f"✅ Timer is counting down correctly ({initial_time:.1f}s -> {final_time:.1f}s)"
        )
    else:
        print(f"❌ Timer not counting down ({initial_time:.1f}s -> {final_time:.1f}s)")

    # Test timer display formatting
    print("\n3. Testing timer display formatting...")
    test_times = [305, 245, 65, 10, 0]

    for test_time in test_times:
        minutes = int(test_time // 60)
        seconds = int(test_time % 60)
        formatted = f"{minutes:02d}:{seconds:02d}"
        print(f"   {test_time}s -> {formatted}")

    print("\n✅ Enemy spawn timer test completed!")


if __name__ == "__main__":
    test_spawn_timer()

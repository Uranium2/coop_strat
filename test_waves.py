#!/usr/bin/env python3
"""
Test script to verify enemy wave spawning
"""

import asyncio

from client.utils.network_manager import NetworkManager


class TestWaves:
    def __init__(self, name):
        self.name = name
        self.nm = NetworkManager()
        self.lobby_id = None
        self.game_state = None
        self.enemy_count = 0
        self.wave_count = 0

        # Register handlers
        self.nm.register_handler("lobby_created", self._on_lobby_created)
        self.nm.register_handler("game_started", self._on_game_started)
        self.nm.register_handler("game_state_update", self._on_game_update)

    def _on_lobby_created(self, data):
        print(f"{self.name}: Lobby created {data['lobby_id']}")
        self.lobby_id = data["lobby_id"]

    def _on_game_started(self, data):
        print(f"{self.name}: Game started!")
        self.game_state = data["game_state"]
        print(f"{self.name}: Heroes: {len(self.game_state['heroes'])}")
        print(f"{self.name}: Initial enemies: {len(self.game_state['enemies'])}")

    def _on_game_update(self, data):
        self.game_state = data["game_state"]
        new_enemy_count = len(self.game_state["enemies"])

        if new_enemy_count > self.enemy_count:
            self.wave_count += 1
            print(f"\n🌊 WAVE {self.wave_count} DETECTED!")
            print(f"Enemy count: {self.enemy_count} -> {new_enemy_count}")
            print(f"New enemies spawned: {new_enemy_count - self.enemy_count}")

            # List enemy types and positions
            enemy_types = {}
            for enemy_id, enemy in self.game_state["enemies"].items():
                if enemy["is_active"]:
                    pos = enemy["position"]
                    health = enemy["health"]
                    # Try to determine enemy type by health (since we don't store type)
                    if health <= 18:  # FAST enemies have 15 + wave scaling
                        enemy_type = "FAST"
                    elif health <= 35:  # BASIC enemies have 30 + wave scaling
                        enemy_type = "BASIC"
                    elif health <= 45:  # RANGED enemies have 20 + wave scaling
                        enemy_type = "RANGED"
                    else:  # HEAVY enemies have 50 + wave scaling
                        enemy_type = "HEAVY"

                    enemy_types[enemy_type] = enemy_types.get(enemy_type, 0) + 1

            print(f"Enemy types in wave: {dict(enemy_types)}")
            self.enemy_count = new_enemy_count
        elif new_enemy_count < self.enemy_count:
            print(f"Enemies defeated: {self.enemy_count} -> {new_enemy_count}")
            self.enemy_count = new_enemy_count

    async def create_lobby(self):
        await self.nm.create_lobby(self.name)

    async def select_hero(self, hero_type="ARCHER"):
        await self.nm.select_hero(hero_type)

    async def start_game(self):
        await self.nm.start_game()

    async def connect(self):
        await self.nm.connect()


async def test_waves():
    print("=== Testing Enemy Wave System ===")

    try:
        player = TestWaves("WaveTest")

        print("\n1. Connecting and creating lobby...")
        await player.connect()
        await player.create_lobby()
        await asyncio.sleep(1)

        if not player.lobby_id:
            print("❌ Failed to create lobby")
            return

        print(f"✓ Lobby created: {player.lobby_id}")

        print("\n2. Selecting hero and starting game...")
        await player.select_hero("ARCHER")  # Use archer for long-range combat
        await player.start_game()
        await asyncio.sleep(2)

        if not player.game_state or not player.game_state.get("is_active"):
            print("❌ Game didn't start properly")
            return

        print("✓ Game started successfully")

        print("\n3. Waiting for enemy waves (15 second intervals)...")
        print("Will wait for 3 waves to test the system...")

        start_time = asyncio.get_event_loop().time()
        target_waves = 3

        while player.wave_count < target_waves:
            await asyncio.sleep(1)
            elapsed = asyncio.get_event_loop().time() - start_time

            if elapsed > 60:  # Max 60 seconds wait
                print(
                    f"❌ Timeout waiting for waves. Only got {player.wave_count}/{target_waves} waves"
                )
                break

            # Show progress every 5 seconds
            if int(elapsed) % 5 == 0:
                print(
                    f"⏱️  Elapsed: {int(elapsed)}s, Waves detected: {player.wave_count}/{target_waves}"
                )

        if player.wave_count >= target_waves:
            print(f"\n✓ SUCCESS! Detected {player.wave_count} enemy waves")
            print(f"Final enemy count: {len(player.game_state['enemies'])}")

        print("\n=== Wave Test Complete ===")

    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_waves())

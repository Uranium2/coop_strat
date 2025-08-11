#!/usr/bin/env python3
"""
Test script to verify enemy death visualization and cleanup
"""

import asyncio
import time

from client.utils.network_manager import NetworkManager


class TestEnemyDeath:
    def __init__(self, name):
        self.name = name
        self.nm = NetworkManager()
        self.lobby_id = None
        self.game_state = None
        self.enemy_death_logged = False

    async def connect(self):
        return await self.nm.connect()

    async def disconnect(self):
        await self.nm.disconnect()

    def register_handlers(self):
        self.nm.register_handler("lobby_created", self._on_lobby_created)
        self.nm.register_handler("game_started", self._on_game_started)
        self.nm.register_handler("game_update", self._on_game_update)

    def _on_lobby_created(self, data):
        print(f"{self.name}: Lobby created {data['lobby_id']}")
        self.lobby_id = data["lobby_id"]

    def _on_game_started(self, data):
        print(f"{self.name}: Game started!")
        self.game_state = data["game_state"]

    def _on_game_update(self, data):
        self.game_state = data["game_state"]

        # Check for dead enemies
        for enemy_id, enemy in self.game_state["enemies"].items():
            if enemy.get("is_dead", False) and not self.enemy_death_logged:
                print(f"✅ Enemy {enemy_id[:8]} died!")
                print(f"   Health: {enemy['health']}")
                print(f"   is_dead: {enemy['is_dead']}")
                print(f"   death_time: {enemy.get('death_time', 'missing')}")
                self.enemy_death_logged = True

    async def create_lobby(self):
        await self.nm.create_lobby(self.name)

    async def select_hero(self, hero_type="TANK"):
        await self.nm.select_hero(hero_type)

    async def start_game(self):
        await self.nm.start_game()


async def test_enemy_death_and_cleanup():
    print("=== Testing Enemy Death Visualization and Cleanup ===")

    player = TestEnemyDeath("TestPlayer")
    player.register_handlers()

    try:
        # Connect and setup
        print("\n1. Setting up game...")
        if not await player.connect():
            print("Failed to connect")
            return

        await player.create_lobby()
        await asyncio.sleep(1)
        await player.select_hero("TANK")
        await asyncio.sleep(0.5)
        await player.start_game()
        await asyncio.sleep(2)

        # Wait for enemy to spawn
        print("\n2. Waiting for enemy to spawn...")
        for i in range(10):
            await asyncio.sleep(1)
            if player.game_state and len(player.game_state["enemies"]) > 0:
                enemy = list(player.game_state["enemies"].values())[0]
                print(
                    f"✓ Enemy spawned at ({enemy['position']['x']}, {enemy['position']['y']})"
                )
                break

        if not player.game_state["enemies"]:
            print("❌ No enemy spawned")
            return

        # Move hero to kill enemy
        print("\n3. Moving hero to kill enemy...")
        enemy = list(player.game_state["enemies"].values())[0]
        enemy_id = list(player.game_state["enemies"].keys())[0]
        enemy_pos = enemy["position"]

        await player.nm.send_game_action(
            {
                "type": "move_hero",
                "target_position": {"x": enemy_pos["x"], "y": enemy_pos["y"]},
            }
        )

        # Wait for combat and death
        print("Waiting for combat and death...")
        death_time = None
        for i in range(20):
            await asyncio.sleep(1)
            if player.enemy_death_logged:
                death_time = time.time()
                break
            print(f"  Waiting {i + 1}/20 seconds...")

        if not player.enemy_death_logged:
            print("❌ Enemy didn't die")
            return

        # Verify enemy is still in game state but marked as dead
        print("\n4. Verifying dead enemy remains visible...")
        await asyncio.sleep(1)

        if enemy_id in player.game_state["enemies"]:
            enemy = player.game_state["enemies"][enemy_id]
            print("✓ Dead enemy still exists in game")
            print(f"   Health: {enemy['health']}")
            print(f"   is_dead: {enemy.get('is_dead', False)}")
        else:
            print("❌ Dead enemy was removed immediately!")
            return

        # Wait for cleanup (5 seconds in test mode)
        print("\n5. Waiting for cleanup after 5 seconds...")
        cleanup_start = time.time()

        while time.time() - cleanup_start < 7:  # Wait up to 7 seconds
            await asyncio.sleep(0.5)
            if enemy_id not in player.game_state["enemies"]:
                elapsed = time.time() - cleanup_start
                print(f"✅ Dead enemy cleaned up after {elapsed:.1f} seconds!")
                break
        else:
            print("❌ Dead enemy was not cleaned up after 7 seconds")
            if enemy_id in player.game_state["enemies"]:
                enemy = player.game_state["enemies"][enemy_id]
                print(
                    f"   Enemy still exists: health={enemy['health']}, is_dead={enemy.get('is_dead', False)}"
                )

        print("\n=== Death and Cleanup Test Complete ===")

    except Exception as e:
        print(f"Test failed with error: {e}")
        import traceback

        traceback.print_exc()
    finally:
        await player.disconnect()


if __name__ == "__main__":
    asyncio.run(test_enemy_death_and_cleanup())

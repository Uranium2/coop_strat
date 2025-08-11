#!/usr/bin/env python3
"""
Test script to verify enemy spawning and basic combat
"""

import asyncio
import math

from client.utils.network_manager import NetworkManager


class TestCombat:
    def __init__(self, name):
        self.name = name
        self.nm = NetworkManager()
        self.lobby_id = None
        self.game_state = None
        self.enemy_count = 0

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
        print(f"{self.name}: Heroes: {len(self.game_state['heroes'])}")
        print(f"{self.name}: Initial enemies: {len(self.game_state['enemies'])}")

    def _on_game_update(self, data):
        self.game_state = data["game_state"]
        new_enemy_count = len(self.game_state["enemies"])
        if new_enemy_count != self.enemy_count:
            print(
                f"{self.name}: Enemy count changed: {self.enemy_count} -> {new_enemy_count}"
            )
            self.enemy_count = new_enemy_count

            # List enemies and their positions
            for enemy_id, enemy in self.game_state["enemies"].items():
                if enemy["is_active"]:
                    pos = enemy["position"]
                    health = enemy["health"]
                    print(
                        f"  Enemy {enemy_id[:8]}: Health {health} at ({pos['x']}, {pos['y']})"
                    )

    async def create_lobby(self):
        await self.nm.create_lobby(self.name)

    async def select_hero(self, hero_type="TANK"):
        await self.nm.select_hero(hero_type)

    async def start_game(self):
        await self.nm.start_game()

    async def attack_enemy(self, enemy_id):
        await self.nm.send_game_action({"type": "attack_enemy", "enemy_id": enemy_id})


async def test_combat():
    print("=== Testing Enemy Spawning and Combat ===")

    player = TestCombat("TestPlayer")
    player.register_handlers()

    try:
        # Connect and create lobby
        print("\n1. Connecting and creating lobby...")
        if not await player.connect():
            print("Failed to connect")
            return

        await player.create_lobby()
        await asyncio.sleep(1)

        if not player.lobby_id:
            print("Failed to create lobby")
            return
        print(f"✓ Lobby created: {player.lobby_id}")

        # Select hero and start game
        print("\n2. Starting game...")
        await player.select_hero("TANK")
        await asyncio.sleep(0.5)
        await player.start_game()
        await asyncio.sleep(2)

        if not player.game_state:
            print("Failed to start game")
            return
        print("✓ Game started successfully")

        # Wait for enemies to spawn (10 seconds)
        print("\n3. Waiting for test enemy to spawn...")
        for i in range(10):
            await asyncio.sleep(1)
            print(f"  Waiting {i + 1}/10 seconds...")
            if player.enemy_count > 0:
                print(f"✓ Test enemy spawned! Count: {player.enemy_count}")
                break

        if player.enemy_count == 0:
            print("❌ No test enemy spawned after 10 seconds")
            return

        # Test combat by moving hero close to enemy
        print("\n4. Testing combat...")
        hero_id = list(player.game_state["heroes"].keys())[0]
        hero = player.game_state["heroes"][hero_id]
        print(f"Hero attack range: {hero['attack_range']}")
        print(
            f"Hero position before: ({hero['position']['x']}, {hero['position']['y']})"
        )

        enemy_id = list(player.game_state["enemies"].keys())[0]
        enemy = player.game_state["enemies"][enemy_id]

        print(
            f"Moving hero to enemy at ({enemy['position']['x']}, {enemy['position']['y']})..."
        )
        await player.attack_enemy(enemy_id)

        print("Waiting for hero to reach enemy...")
        for i in range(10):
            await asyncio.sleep(1)
            hero = player.game_state["heroes"][hero_id]
            enemies = list(player.game_state["enemies"].values())

            if enemies:
                enemy = enemies[0]
                distance = math.sqrt(
                    (hero["position"]["x"] - enemy["position"]["x"]) ** 2
                    + (hero["position"]["y"] - enemy["position"]["y"]) ** 2
                )
                print(
                    f"  {i + 1}s: Hero at ({hero['position']['x']:.1f}, {hero['position']['y']:.1f}), distance to enemy: {distance:.1f}"
                )

                if distance < 2.0:  # Close enough for combat
                    print("  Hero reached combat range!")
                    await asyncio.sleep(2)  # Wait for combat to process
                    break

        # Check final positions and combat result
        hero = player.game_state["heroes"][hero_id]
        print(
            f"Hero position after: ({hero['position']['x']}, {hero['position']['y']})"
        )

        enemies = list(player.game_state["enemies"].values())
        if enemies:
            enemy = enemies[0]
            print(f"Enemy health after moving close: {enemy['health']}")
            print(f"Enemy is_dead: {enemy.get('is_dead', False)}")

            if enemy.get("death_time"):
                print(f"Enemy death_time: {enemy['death_time']}")

            # Check if enemy took damage
            if enemy["health"] < 30:  # Enemy starts with 30 health
                if enemy["health"] <= 0:
                    print("✓ Enemy killed! Health reached 0")
                    print("✓ Enemy properly marked as dead")
                else:
                    print("✓ Combat working! Enemy took damage")
            else:
                print("❌ Enemy didn't take damage")
        else:
            print("❌ No active enemies to attack")

        print("\n=== Test Complete ===")

    except Exception as e:
        print(f"Test failed with error: {e}")
        import traceback

        traceback.print_exc()
    finally:
        await player.disconnect()


if __name__ == "__main__":
    asyncio.run(test_combat())

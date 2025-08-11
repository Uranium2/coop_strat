#!/usr/bin/env python3
"""
Test script to verify that different hero types have different attack ranges
"""

import asyncio
import json

import websockets

from shared.models.game_models import HeroType


class RangeTestClient:
    def __init__(self):
        self.player_id = None
        self.lobby_id = None
        self.game_state = None

    async def connect_and_test(self, hero_type: HeroType, test_distance: float):
        uri = "ws://localhost:8000/ws"
        print(f"\nTesting {hero_type.value} attack range at distance {test_distance}")

        try:
            async with websockets.connect(uri) as websocket:
                # Create lobby
                create_lobby_msg = {
                    "type": "create_lobby",
                    "player_name": f"RangeTest_{hero_type.value}",
                    "hero_type": hero_type.value,
                }
                await websocket.send(json.dumps(create_lobby_msg))
                response = await websocket.recv()
                lobby_data = json.loads(response)

                if lobby_data["type"] != "lobby_created":
                    print(f"❌ Failed to create lobby: {lobby_data}")
                    return False

                self.lobby_id = lobby_data["lobby_id"]
                self.player_id = lobby_data["player_id"]
                print(f"✓ Lobby created: {self.lobby_id}")

                # Start game
                start_msg = {"type": "start_game"}
                await websocket.send(json.dumps(start_msg))

                # Wait for game to start and get initial state
                for _ in range(5):
                    response = await websocket.recv()
                    data = json.loads(response)
                    if data["type"] == "game_state_update":
                        self.game_state = data["game_state"]
                        if self.game_state.get("is_active"):
                            break

                if not self.game_state or not self.game_state.get("is_active"):
                    print("❌ Game didn't start properly")
                    return False

                print("✓ Game started")

                # Wait for enemy to spawn
                print("Waiting for enemy to spawn...")
                enemy_id = None
                for wait_time in range(10):
                    await asyncio.sleep(1)
                    response = await websocket.recv()
                    data = json.loads(response)
                    if data["type"] == "game_state_update":
                        enemies = data["game_state"].get("enemies", {})
                        if enemies:
                            enemy_id = list(enemies.keys())[0]
                            enemy = enemies[enemy_id]
                            print(
                                f"✓ Enemy spawned at ({enemy['position']['x']}, {enemy['position']['y']})"
                            )
                            break

                if not enemy_id:
                    print("❌ No enemy spawned")
                    return False

                # Position hero at test distance from enemy
                enemy = self.game_state["enemies"][enemy_id]
                enemy_x, enemy_y = enemy["position"]["x"], enemy["position"]["y"]

                # Calculate position at test_distance from enemy
                hero_x = enemy_x - test_distance
                hero_y = enemy_y

                print(f"Positioning hero at distance {test_distance} from enemy")
                print(f"Enemy at ({enemy_x}, {enemy_y}), Hero at ({hero_x}, {hero_y})")

                # Move hero to test position
                move_msg = {"type": "move_hero", "position": {"x": hero_x, "y": hero_y}}
                await websocket.send(json.dumps(move_msg))

                # Wait and check if combat occurred
                combat_occurred = False
                initial_enemy_health = enemy["health"]

                for check_time in range(5):
                    await asyncio.sleep(1)
                    response = await websocket.recv()
                    data = json.loads(response)
                    if data["type"] == "game_state_update":
                        current_enemies = data["game_state"].get("enemies", {})
                        if enemy_id in current_enemies:
                            current_enemy = current_enemies[enemy_id]
                            if current_enemy["health"] < initial_enemy_health:
                                combat_occurred = True
                                print(
                                    f"✓ Combat occurred! Enemy health: {initial_enemy_health} → {current_enemy['health']}"
                                )
                                break

                return combat_occurred

        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False


async def test_attack_ranges():
    print("=== Testing Attack Ranges ===")

    # Test different hero types at different distances
    tests = [
        (HeroType.TANK, 1.8),  # Tank range: 2.0, should hit at 1.8
        (HeroType.TANK, 2.2),  # Tank range: 2.0, should miss at 2.2
        (HeroType.ARCHER, 8.0),  # Archer range: 10.0, should hit at 8.0
        (HeroType.ARCHER, 12.0),  # Archer range: 10.0, should miss at 12.0
        (HeroType.MAGE, 6.0),  # Mage range: 8.0, should hit at 6.0
        (HeroType.MAGE, 9.0),  # Mage range: 8.0, should miss at 9.0
    ]

    results = []
    for hero_type, distance in tests:
        client = RangeTestClient()
        combat_occurred = await client.connect_and_test(hero_type, distance)
        results.append((hero_type, distance, combat_occurred))
        await asyncio.sleep(1)  # Brief pause between tests

    print("\n=== Results ===")
    for hero_type, distance, combat_occurred in results:
        status = "✓ HIT" if combat_occurred else "✗ MISS"
        print(f"{hero_type.value} at distance {distance}: {status}")


if __name__ == "__main__":
    asyncio.run(test_attack_ranges())

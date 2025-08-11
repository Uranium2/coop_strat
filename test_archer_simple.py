#!/usr/bin/env python3
"""
Simple test to verify archer can attack from longer range
"""

import asyncio
import json

import websockets


async def test_archer_range():
    uri = "ws://localhost:8000/ws"
    print("Testing ARCHER attack range (should be 10.0)")

    try:
        async with websockets.connect(uri) as websocket:
            # Create lobby with archer
            create_lobby_msg = {
                "type": "create_lobby",
                "player_name": "ArcherTest",
                "hero_type": "ARCHER",
            }
            await websocket.send(json.dumps(create_lobby_msg))
            response = await websocket.recv()
            lobby_data = json.loads(response)

            lobby_id = lobby_data["lobby_id"]
            print(f"✓ Lobby created: {lobby_id}")

            # Start game
            start_msg = {"type": "start_game"}
            await websocket.send(json.dumps(start_msg))

            # Wait for game to start
            game_state = None
            for _ in range(5):
                response = await websocket.recv()
                data = json.loads(response)
                if data["type"] == "game_state_update":
                    game_state = data["game_state"]
                    if game_state.get("is_active"):
                        print("✓ Game started")
                        break

            # Get hero stats
            heroes = game_state["heroes"]
            hero = list(heroes.values())[0]
            print(f"Hero attack range: {hero['attack_range']}")
            print(f"Hero position: ({hero['position']['x']}, {hero['position']['y']})")

            # Wait for enemy
            print("Waiting for enemy...")
            enemy = None
            for _ in range(10):
                await asyncio.sleep(1)
                response = await websocket.recv()
                data = json.loads(response)
                if data["type"] == "game_state_update":
                    enemies = data["game_state"].get("enemies", {})
                    if enemies:
                        enemy = list(enemies.values())[0]
                        print(
                            f"✓ Enemy spawned at ({enemy['position']['x']}, {enemy['position']['y']})"
                        )
                        break

            if not enemy:
                print("❌ No enemy spawned")
                return

            # Move archer to exactly 9 tiles away (within range of 10)
            enemy_x, enemy_y = enemy["position"]["x"], enemy["position"]["y"]
            archer_x = enemy_x - 9.0  # 9 tiles away horizontally
            archer_y = enemy_y

            print(
                f"Moving archer to ({archer_x}, {archer_y}) - distance 9.0 from enemy"
            )

            move_msg = {"type": "move_hero", "position": {"x": archer_x, "y": archer_y}}
            await websocket.send(json.dumps(move_msg))

            # Wait for movement and combat
            initial_enemy_health = enemy["health"]
            print(f"Initial enemy health: {initial_enemy_health}")

            for i in range(10):
                await asyncio.sleep(1)
                response = await websocket.recv()
                data = json.loads(response)
                if data["type"] == "game_state_update":
                    current_enemies = data["game_state"].get("enemies", {})
                    current_heroes = data["game_state"].get("heroes", {})

                    if current_enemies:
                        current_enemy = list(current_enemies.values())[0]
                        current_hero = list(current_heroes.values())[0]

                        # Calculate actual distance
                        hx, hy = (
                            current_hero["position"]["x"],
                            current_hero["position"]["y"],
                        )
                        ex, ey = (
                            current_enemy["position"]["x"],
                            current_enemy["position"]["y"],
                        )
                        distance = ((hx - ex) ** 2 + (hy - ey) ** 2) ** 0.5

                        print(
                            f"Hero at ({hx:.1f}, {hy:.1f}), Enemy at ({ex:.1f}, {ey:.1f}), Distance: {distance:.1f}"
                        )
                        print(f"Enemy health: {current_enemy['health']}")

                        if current_enemy["health"] < initial_enemy_health:
                            print(
                                f"✓ SUCCESS! Archer attacked from distance {distance:.1f}"
                            )
                            print(
                                f"Enemy health dropped from {initial_enemy_health} to {current_enemy['health']}"
                            )
                            return

            print("❌ No combat occurred within 10 seconds")

    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(test_archer_range())

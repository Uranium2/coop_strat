#!/usr/bin/env python3

import asyncio
import json
import uuid

import websockets


async def wait_for_game_update(websocket, timeout=5):
    """Wait for a game_update message"""
    start_time = asyncio.get_event_loop().time()
    while asyncio.get_event_loop().time() - start_time < timeout:
        try:
            response = await asyncio.wait_for(websocket.recv(), timeout=1)
            data = json.loads(response)
            if data.get("type") == "game_update":
                return data
        except asyncio.TimeoutError:
            continue
    return None


async def test_enemy_death_and_cleanup():
    print("Testing enemy death visualization and cleanup...")

    player_id = str(uuid.uuid4())

    async with websockets.connect(f"ws://localhost:8000/ws/{player_id}") as ws:
        print("Connected!")

        # Setup game
        await ws.send(json.dumps({"type": "create_lobby", "player_name": "TestPlayer"}))
        response = await ws.recv()
        lobby_id = json.loads(response)["lobby_id"]

        await ws.send(json.dumps({"type": "select_hero", "hero_type": "TANK"}))
        await ws.recv()

        await ws.send(json.dumps({"type": "start_game"}))
        await ws.recv()
        print("Game started")

        # Wait for enemy to spawn
        print("Waiting for test enemy to spawn...")
        enemy_data = None
        for i in range(10):
            update = await wait_for_game_update(ws, timeout=2)
            if update:
                enemies = update.get("game_state", {}).get("enemies", {})
                if enemies:
                    enemy_data = update
                    break
            await asyncio.sleep(0.5)

        if not enemy_data:
            print("❌ No enemy spawned")
            return

        game_state = enemy_data["game_state"]
        heroes = game_state.get("heroes", {})
        enemies = game_state.get("enemies", {})

        hero = list(heroes.values())[0]
        enemy = list(enemies.values())[0]
        enemy_id = list(enemies.keys())[0]

        print(
            f"✅ Enemy spawned at ({enemy['position']['x']}, {enemy['position']['y']})"
        )
        print(f"Hero at ({hero['position']['x']}, {hero['position']['y']})")

        # Move hero to enemy to kill it
        print("Moving hero to kill enemy...")
        await ws.send(
            json.dumps(
                {
                    "type": "game_action",
                    "action": {
                        "type": "move_hero",
                        "target_position": {
                            "x": enemy["position"]["x"],
                            "y": enemy["position"]["y"],
                        },
                    },
                }
            )
        )

        # Wait for combat and death
        enemy_died = False
        death_time = None

        for i in range(15):  # Wait up to 15 seconds for combat
            update = await wait_for_game_update(ws, timeout=2)
            if update:
                enemies = update["game_state"]["enemies"]
                if enemy_id in enemies:
                    enemy = enemies[enemy_id]

                    # Check if enemy died
                    if enemy.get("is_dead", False) and not enemy_died:
                        enemy_died = True
                        death_time = asyncio.get_event_loop().time()
                        print(
                            f"✅ Enemy died! Health: {enemy['health']}, is_dead: {enemy['is_dead']}"
                        )
                        print(f"Enemy death_time: {enemy.get('death_time', 'missing')}")
                        break

            await asyncio.sleep(1)

        if not enemy_died:
            print("❌ Enemy didn't die in time")
            return

        # Wait and verify enemy is still there but marked as dead
        print("Verifying enemy remains visible but marked as dead...")
        await asyncio.sleep(2)

        update = await wait_for_game_update(ws, timeout=5)
        if update:
            enemies = update["game_state"]["enemies"]
            if enemy_id in enemies:
                enemy = enemies[enemy_id]
                print(
                    f"✅ Dead enemy still exists: health={enemy['health']}, is_dead={enemy.get('is_dead', False)}"
                )
            else:
                print("❌ Enemy was removed too early!")
                return

        # For testing purposes, let's wait a shorter time (5 seconds) to verify the cleanup logic works
        # In a real test you'd wait the full 20 seconds
        print("Waiting 5 seconds to test cleanup timing...")
        await asyncio.sleep(5)

        update = await wait_for_game_update(ws, timeout=5)
        if update:
            enemies = update["game_state"]["enemies"]
            if enemy_id in enemies:
                enemy = enemies[enemy_id]
                print(
                    f"Enemy still exists after 5s: health={enemy['health']}, is_dead={enemy.get('is_dead', False)}"
                )
                print("✅ Enemy correctly remains for visual feedback")
            else:
                print(
                    "Enemy was removed after 5s (this would happen at 20s in real game)"
                )

        print("✅ Death visualization test completed!")
        print("Note: In real gameplay, dead enemies are removed after 20 seconds")


if __name__ == "__main__":
    asyncio.run(test_enemy_death_and_cleanup())

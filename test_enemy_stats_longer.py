#!/usr/bin/env python3

import asyncio
import json
import uuid

import websockets


async def test_enemy_stats_longer():
    player_id = str(uuid.uuid4())
    uri = f"ws://localhost:8000/ws/{player_id}"

    print(f"Testing enemy stats at {uri}")

    async with websockets.connect(uri) as websocket:
        print("Connected successfully!")

        # Create lobby
        await websocket.send(
            json.dumps({"type": "create_lobby", "player_name": "TestPlayer"})
        )

        response = await websocket.recv()
        data = json.loads(response)
        lobby_id = data["lobby_id"]
        print(f"Created lobby: {lobby_id}")

        # Choose hero type
        await websocket.send(json.dumps({"type": "select_hero", "hero_type": "TANK"}))

        response = await websocket.recv()
        print(f"Hero selection response: {json.loads(response)}")

        # Start game
        await websocket.send(json.dumps({"type": "start_game"}))

        response = await websocket.recv()
        data = json.loads(response)
        print(f"Game start response: {data['type']}")

        # Wait for game state updates and check enemies (wait up to 20 seconds)
        for i in range(25):
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                data = json.loads(response)

                if data["type"] == "game_state":
                    game_state = data["game_state"]
                    heroes = game_state.get("heroes", {})
                    enemies = game_state.get("enemies", {})

                    print(
                        f"Game time: {game_state.get('game_time', 0):.1f}s, Heroes: {len(heroes)}, Enemies: {len(enemies)}"
                    )

                    if heroes:
                        hero = list(heroes.values())[0]
                        print(
                            f"Hero stats: health={hero['health']}, attack_damage={hero.get('attack_damage', 'missing')}, speed={hero.get('speed', 'missing')}, attack_range={hero.get('attack_range', 'missing')}"
                        )

                    if enemies:
                        enemy = list(enemies.values())[0]
                        print(
                            f"Enemy stats: health={enemy['health']}, attack_damage={enemy.get('attack_damage', 'missing')}, speed={enemy.get('speed', 'missing')}, attack_range={enemy.get('attack_range', 'missing')}"
                        )
                        print("✅ Found enemies with stats!")
                        break

            except asyncio.TimeoutError:
                print(f"Waiting for enemies to spawn... ({i + 1}/25)")
                continue

        print("✅ Enemy stats test completed!")


if __name__ == "__main__":
    asyncio.run(test_enemy_stats_longer())

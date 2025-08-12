#!/usr/bin/env python3

import asyncio
import json
import sys

sys.path.append(".")

import websockets


async def test_building_coordinate_system():
    """Test building placement with coordinate debugging"""

    print("🔍 Testing building coordinate system...")

    # Connect to server
    player_id = "test_player_123"
    uri = f"ws://localhost:8000/ws/{player_id}"

    try:
        async with websockets.connect(uri) as websocket:
            # Create lobby first
            await websocket.send(
                json.dumps({"type": "create_lobby", "player_name": "TestPlayer"})
            )
            response = await websocket.recv()
            print(f"Create lobby response: {response}")

            # Join lobby and start game
            await websocket.send(
                json.dumps({"type": "join_lobby", "hero_type": "WARRIOR"})
            )
            response = await websocket.recv()
            print(f"Join lobby response: {response}")

            await websocket.send(json.dumps({"type": "start_game"}))
            response = await websocket.recv()
            print(f"Start game response: {response}")

            # Wait for initial game state
            await asyncio.sleep(1)

            # Get initial game state
            response = await websocket.recv()
            game_state = json.loads(response)

            if "game_state" not in game_state:
                print("❌ No game state received")
                return

            state = game_state["game_state"]
            heroes = state.get("heroes", {})

            if not heroes:
                print("❌ No heroes found")
                return

            # Get hero position
            hero = list(heroes.values())[0]
            hero_pos = hero["position"]
            print(f"🧙 Hero position: x={hero_pos['x']}, y={hero_pos['y']}")

            # Move hero to a specific location (tile coordinates)
            target_x = hero_pos["x"] + 3
            target_y = hero_pos["y"] + 1
            print(f"🎯 Moving hero to: x={target_x}, y={target_y}")

            move_action = {
                "type": "move_hero",
                "target_position": {"x": target_x, "y": target_y},
            }
            await websocket.send(
                json.dumps({"type": "game_action", "action": move_action})
            )

            # Wait for hero to arrive
            for i in range(10):  # Wait up to 10 seconds
                response = await websocket.recv()
                game_state = json.loads(response)

                if "game_state" in game_state:
                    state = game_state["game_state"]
                    heroes = state.get("heroes", {})
                    if heroes:
                        hero = list(heroes.values())[0]
                        new_pos = hero["position"]
                        distance = (
                            (new_pos["x"] - target_x) ** 2
                            + (new_pos["y"] - target_y) ** 2
                        ) ** 0.5
                        print(
                            f"🚶 Hero moving: x={new_pos['x']:.2f}, y={new_pos['y']:.2f}, distance to target: {distance:.2f}"
                        )

                        if distance < 0.6:  # Hero reached target
                            print("✅ Hero arrived at target!")
                            break
                await asyncio.sleep(1)

            # Now try to build at hero's current location
            current_response = await websocket.recv()
            game_state = json.loads(current_response)

            if "game_state" in game_state:
                state = game_state["game_state"]
                heroes = state.get("heroes", {})
                if heroes:
                    hero = list(heroes.values())[0]
                    hero_pos = hero["position"]

                    # Try building at exact hero position (should work)
                    build_x = int(hero_pos["x"])
                    build_y = int(hero_pos["y"])

                    print(
                        f"🏗️ Attempting to build at hero location: x={build_x}, y={build_y}"
                    )
                    print(
                        f"   Hero actual position: x={hero_pos['x']:.2f}, y={hero_pos['y']:.2f}"
                    )

                    build_action = {
                        "type": "build",
                        "building_type": "WALL",
                        "position": {"x": build_x, "y": build_y},
                    }
                    await websocket.send(
                        json.dumps({"type": "game_action", "action": build_action})
                    )

                    # Check if building was created
                    for i in range(5):
                        response = await websocket.recv()
                        game_state = json.loads(response)

                        if "game_state" in game_state:
                            state = game_state["game_state"]
                            buildings = state.get("buildings", {})
                            new_buildings = [
                                b
                                for b in buildings.values()
                                if b.get("building_type") == "WALL"
                            ]

                            if new_buildings:
                                building = new_buildings[0]
                                building_pos = building["position"]
                                print(
                                    f"🏢 Building created at: x={building_pos['x']}, y={building_pos['y']}"
                                )
                                print("✅ Building placement successful!")
                                return
                            else:
                                print(f"⏳ Waiting for building... ({i + 1}/5)")

                        await asyncio.sleep(1)

                    print(
                        "❌ Building was not created - checking server logs for rejection reason"
                    )

    except Exception as e:
        print(f"❌ Connection error: {e}")


if __name__ == "__main__":
    asyncio.run(test_building_coordinate_system())

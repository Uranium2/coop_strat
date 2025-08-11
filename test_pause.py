#!/usr/bin/env python3

import asyncio
import json
import uuid

import websockets


async def test_pause_functionality():
    player_id = str(uuid.uuid4())
    uri = f"ws://localhost:8000/ws/{player_id}"

    print(f"Testing pause functionality at {uri}")

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

        # Wait for initial game state
        initial_time = None
        for i in range(5):
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                data = json.loads(response)

                if data["type"] == "game_state":
                    game_state = data["game_state"]
                    if initial_time is None:
                        initial_time = game_state.get("game_time", 0)
                        is_paused = game_state.get("is_paused", False)
                        print(
                            f"Initial game time: {initial_time:.2f}s, Paused: {is_paused}"
                        )
                        break

            except asyncio.TimeoutError:
                print(f"Waiting for initial game state... ({i + 1}/5)")
                continue

        if initial_time is None:
            print("❌ Could not get initial game state")
            return

        # Test pause toggle
        print("Sending pause toggle...")
        await websocket.send(
            json.dumps({"type": "game_action", "action": {"type": "toggle_pause"}})
        )

        # Wait for pause state update
        pause_confirmed = False
        for i in range(10):
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                data = json.loads(response)

                if data["type"] == "game_update":
                    game_state = data["game_state"]
                    is_paused = game_state.get("is_paused", False)
                    game_time = game_state.get("game_time", 0)

                    if is_paused:
                        print(f"✅ Game successfully paused! Time: {game_time:.2f}s")
                        pause_confirmed = True
                        break

            except asyncio.TimeoutError:
                print(f"Waiting for pause confirmation... ({i + 1}/10)")
                continue

        if not pause_confirmed:
            print("❌ Pause was not confirmed")
            return

        # Wait a bit more and check that time doesn't advance much when paused
        await asyncio.sleep(2)

        # Get another game state to verify time didn't advance much
        for i in range(5):
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                data = json.loads(response)

                if data["type"] == "game_update":
                    game_state = data["game_state"]
                    is_paused = game_state.get("is_paused", False)
                    final_time = game_state.get("game_time", 0)

                    if is_paused:
                        time_diff = final_time - initial_time
                        print(f"Time difference while paused: {time_diff:.2f}s")

                        if time_diff < 0.5:  # Should be very small time difference
                            print("✅ Game logic is properly paused!")
                        else:
                            print("❌ Game logic is still running while paused")
                        break

            except asyncio.TimeoutError:
                continue

        # Test unpause
        print("Sending unpause toggle...")
        await websocket.send(
            json.dumps({"type": "game_action", "action": {"type": "toggle_pause"}})
        )

        # Wait for unpause confirmation
        for i in range(5):
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                data = json.loads(response)

                if data["type"] == "game_update":
                    game_state = data["game_state"]
                    is_paused = game_state.get("is_paused", False)

                    if not is_paused:
                        print("✅ Game successfully unpaused!")
                        break

            except asyncio.TimeoutError:
                continue

        print("✅ Pause functionality test completed!")


if __name__ == "__main__":
    asyncio.run(test_pause_functionality())

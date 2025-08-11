#!/usr/bin/env python3

import asyncio
import json
import uuid

import websockets


async def test_pause_simple():
    player_id = str(uuid.uuid4())
    uri = f"ws://localhost:8000/ws/{player_id}"

    print(f"Testing pause at {uri}")

    async with websockets.connect(uri) as websocket:
        print("Connected!")

        # Create lobby
        await websocket.send(
            json.dumps({"type": "create_lobby", "player_name": "TestPlayer"})
        )

        response = await websocket.recv()
        data = json.loads(response)
        lobby_id = data["lobby_id"]
        print(f"Lobby: {lobby_id}")

        # Choose hero and start game
        await websocket.send(json.dumps({"type": "select_hero", "hero_type": "TANK"}))
        await websocket.recv()

        await websocket.send(json.dumps({"type": "start_game"}))
        await websocket.recv()

        # Send pause command
        print("Sending pause...")
        await websocket.send(
            json.dumps({"type": "game_action", "action": {"type": "toggle_pause"}})
        )

        # Check for any response
        try:
            response = await asyncio.wait_for(websocket.recv(), timeout=3.0)
            data = json.loads(response)
            print(f"Response: {data.get('type', 'unknown')}")

            if "game_state" in data:
                is_paused = data["game_state"].get("is_paused", False)
                print(f"Paused: {is_paused}")
                if is_paused:
                    print("✅ Pause worked!")
                else:
                    print("❌ Not paused")

        except asyncio.TimeoutError:
            print("❌ No response to pause command")


if __name__ == "__main__":
    asyncio.run(test_pause_simple())

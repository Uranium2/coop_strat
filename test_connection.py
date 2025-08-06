#!/usr/bin/env python3

import asyncio
import json
import uuid

import websockets


async def test_server():
    player_id = str(uuid.uuid4())
    uri = f"ws://localhost:8000/ws/{player_id}"

    print(f"Testing connection to {uri}")

    try:
        async with websockets.connect(uri) as websocket:
            print("Connected successfully!")

            # Test lobby creation
            create_message = {"type": "create_lobby", "player_name": "TestPlayer"}

            print(f"Sending: {create_message}")
            await websocket.send(json.dumps(create_message))

            # Wait for response
            response = await asyncio.wait_for(websocket.recv(), timeout=5)
            print(f"Received: {response}")

            data = json.loads(response)
            if data.get("type") == "lobby_created":
                print("✅ Lobby creation successful!")
                lobby_id = data.get("lobby_id")
                print(f"Lobby ID: {lobby_id}")
            else:
                print("❌ Unexpected response")

    except Exception as e:
        print(f"❌ Connection failed: {e}")


if __name__ == "__main__":
    asyncio.run(test_server())

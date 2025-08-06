#!/usr/bin/env python3
"""
Test script to isolate the start game issue
"""

import asyncio
import json
import uuid

import websockets


async def test_start_game():
    player_id = str(uuid.uuid4())
    uri = f"ws://localhost:8000/ws/{player_id}"

    try:
        async with websockets.connect(uri) as websocket:
            print("Connected to server")

            # Create lobby
            await websocket.send(
                json.dumps({"type": "create_lobby", "player_name": "TestPlayer"})
            )

            # Wait for lobby creation
            response = await websocket.recv()
            data = json.loads(response)
            print(f"Received: {data}")

            if data.get("type") == "lobby_created":
                lobby_id = data["lobby_id"]
                print(f"Lobby created: {lobby_id}")

                # Select hero
                await websocket.send(
                    json.dumps({"type": "select_hero", "hero_type": "TANK"})
                )

                # Wait for hero selection confirmation
                response = await websocket.recv()
                data = json.loads(response)
                print(f"Hero selection response: {data}")

                # Try to start game
                print("Attempting to start game...")
                await websocket.send(json.dumps({"type": "start_game"}))

                # Wait for game start response
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    data = json.loads(response)
                    print(f"Game start response: {data}")

                    if data.get("type") == "game_started":
                        print("✓ Game started successfully!")
                    else:
                        print(f"✗ Unexpected response: {data}")

                except asyncio.TimeoutError:
                    print("✗ No response to start_game within 5 seconds")

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(test_start_game())

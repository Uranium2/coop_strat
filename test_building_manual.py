#!/usr/bin/env python3

import asyncio
import json

import websockets


async def test_building_placement():
    """Test building placement with the running server"""

    uri = "ws://localhost:8000/ws"

    try:
        print("🔌 Connecting to server...")
        async with websockets.connect(uri) as websocket:
            # Join lobby and start game
            print("🎮 Setting up test game...")

            # Join lobby
            await websocket.send(
                json.dumps(
                    {
                        "type": "join_lobby",
                        "data": {"lobby_id": "test-lobby", "hero_type": "WARRIOR"},
                    }
                )
            )

            # Wait for response
            response = await websocket.recv()
            print(f"Join response: {response}")

            # Start game
            await websocket.send(json.dumps({"type": "start_game"}))

            # Wait for game start
            response = await websocket.recv()
            print(f"Start game response: {response}")

            # Wait a bit for game to initialize
            await asyncio.sleep(1)

            print("🏗️ Testing building placement...")

            # Try to place a building at tile (95, 97) - should be where hero is
            # Convert to pixel coordinates: 95*32=3040, 97*32=3104
            build_action = {
                "type": "build",
                "building_type": "ARCHERY_RANGE",
                "position": {"x": 3040, "y": 3104},
            }

            print(f"📦 Sending build command: {build_action}")
            await websocket.send(json.dumps(build_action))

            # Wait for build response
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                print(f"Build response: {response}")
            except asyncio.TimeoutError:
                print("⏰ No build response received within 5 seconds")

            print("✅ Test completed")

    except Exception as e:
        print(f"❌ Test failed: {e}")


if __name__ == "__main__":
    asyncio.run(test_building_placement())

#!/usr/bin/env python3

import asyncio
import json
import uuid

import websockets


async def test_pause_unpause():
    player_id = str(uuid.uuid4())
    uri = f"ws://localhost:8000/ws/{player_id}"

    print(f"Testing pause/unpause at {uri}")

    async with websockets.connect(uri) as websocket:
        print("Connected!")

        # Create lobby and start game
        await websocket.send(
            json.dumps({"type": "create_lobby", "player_name": "TestPlayer"})
        )
        response = await websocket.recv()
        lobby_id = json.loads(response)["lobby_id"]
        print(f"Lobby: {lobby_id}")

        await websocket.send(json.dumps({"type": "select_hero", "hero_type": "TANK"}))
        await websocket.recv()

        await websocket.send(json.dumps({"type": "start_game"}))
        await websocket.recv()

        # Test pause
        print("1. Pausing game...")
        await websocket.send(
            json.dumps({"type": "game_action", "action": {"type": "toggle_pause"}})
        )

        response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
        data = json.loads(response)
        is_paused = data["game_state"].get("is_paused", False)
        print(
            f"   Paused: {is_paused} ✅" if is_paused else f"   Paused: {is_paused} ❌"
        )

        # Test unpause
        print("2. Unpausing game...")
        await websocket.send(
            json.dumps({"type": "game_action", "action": {"type": "toggle_pause"}})
        )

        response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
        data = json.loads(response)
        is_paused = data["game_state"].get("is_paused", False)
        print(
            f"   Paused: {is_paused} ✅"
            if not is_paused
            else f"   Still paused: {is_paused} ❌"
        )

        # Test pause again
        print("3. Pausing again...")
        await websocket.send(
            json.dumps({"type": "game_action", "action": {"type": "toggle_pause"}})
        )

        response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
        data = json.loads(response)
        is_paused = data["game_state"].get("is_paused", False)
        print(
            f"   Paused: {is_paused} ✅"
            if is_paused
            else f"   Not paused: {is_paused} ❌"
        )

        print("✅ Pause/unpause toggle test completed!")


if __name__ == "__main__":
    asyncio.run(test_pause_unpause())

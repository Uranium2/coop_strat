#!/usr/bin/env python3

import asyncio
import json
import uuid

import websockets


async def test_multiplayer_pause():
    print("Testing multiplayer pause functionality...")

    # Create two players
    player1_id = str(uuid.uuid4())
    player2_id = str(uuid.uuid4())

    async with (
        websockets.connect(f"ws://localhost:8000/ws/{player1_id}") as ws1,
        websockets.connect(f"ws://localhost:8000/ws/{player2_id}") as ws2,
    ):
        print("Both players connected!")

        # Player 1 creates lobby
        await ws1.send(json.dumps({"type": "create_lobby", "player_name": "Player1"}))
        response = await ws1.recv()
        lobby_id = json.loads(response)["lobby_id"]
        print(f"Player 1 created lobby: {lobby_id}")

        # Player 2 joins lobby
        await ws2.send(
            json.dumps(
                {"type": "join_lobby", "lobby_id": lobby_id, "player_name": "Player2"}
            )
        )
        await ws2.recv()
        print("Player 2 joined lobby")

        # Both select heroes
        await ws1.send(json.dumps({"type": "select_hero", "hero_type": "TANK"}))
        await ws1.recv()
        await ws2.send(json.dumps({"type": "select_hero", "hero_type": "ARCHER"}))
        await ws2.recv()
        print("Both players selected heroes")

        # Player 1 starts game
        await ws1.send(json.dumps({"type": "start_game"}))
        await ws1.recv()
        await ws2.recv()  # Player 2 gets game started message
        print("Game started")

        # Player 1 pauses the game
        print("Player 1 pausing game...")
        await ws1.send(
            json.dumps({"type": "game_action", "action": {"type": "toggle_pause"}})
        )

        # Both players should receive pause update
        response1 = await asyncio.wait_for(ws1.recv(), timeout=2.0)
        response2 = await asyncio.wait_for(ws2.recv(), timeout=2.0)

        data1 = json.loads(response1)
        data2 = json.loads(response2)

        print(f"Player 1 received: {data1.get('type', 'unknown')}")
        print(f"Player 2 received: {data2.get('type', 'unknown')}")

        # Check pause state
        pause1 = False
        pause2 = False

        if "game_state" in data1:
            pause1 = data1["game_state"].get("is_paused", False)
        elif data1.get("type") == "game_update":
            pause1 = data1.get("game_state", {}).get("is_paused", False)

        if "game_state" in data2:
            pause2 = data2["game_state"].get("is_paused", False)
        elif data2.get("type") == "game_update":
            pause2 = data2.get("game_state", {}).get("is_paused", False)

        print(f"Player 1 sees paused: {pause1}")
        print(f"Player 2 sees paused: {pause2}")

        if pause1 and pause2:
            print("✅ Both players see the game is paused!")

            # Player 2 unpauses the game
            print("Player 2 unpausing game...")
            await ws2.send(
                json.dumps({"type": "game_action", "action": {"type": "toggle_pause"}})
            )

            # Both players should receive unpause update
            response1 = await asyncio.wait_for(ws1.recv(), timeout=2.0)
            response2 = await asyncio.wait_for(ws2.recv(), timeout=2.0)

            data1 = json.loads(response1)
            data2 = json.loads(response2)

            pause1 = data1.get("game_state", {}).get("is_paused", True)
            pause2 = data2.get("game_state", {}).get("is_paused", True)

            print(f"Player 1 sees paused: {pause1}")
            print(f"Player 2 sees paused: {pause2}")

            if not pause1 and not pause2:
                print("✅ Both players see the game is unpaused!")
            else:
                print("❌ Unpause state not synchronized")
        else:
            print("❌ Pause state not synchronized")

        print("✅ Multiplayer pause test completed!")


if __name__ == "__main__":
    asyncio.run(test_multiplayer_pause())

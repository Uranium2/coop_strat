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


async def test_multiplayer_pause_robust():
    print("Testing multiplayer pause functionality...")

    player1_id = str(uuid.uuid4())
    player2_id = str(uuid.uuid4())

    async with (
        websockets.connect(f"ws://localhost:8000/ws/{player1_id}") as ws1,
        websockets.connect(f"ws://localhost:8000/ws/{player2_id}") as ws2,
    ):
        print("Both players connected!")

        # Setup lobby and game
        await ws1.send(json.dumps({"type": "create_lobby", "player_name": "Player1"}))
        response = await ws1.recv()
        lobby_id = json.loads(response)["lobby_id"]

        await ws2.send(
            json.dumps(
                {"type": "join_lobby", "lobby_id": lobby_id, "player_name": "Player2"}
            )
        )
        await ws2.recv()

        await ws1.send(json.dumps({"type": "select_hero", "hero_type": "TANK"}))
        await ws1.recv()
        await ws2.send(json.dumps({"type": "select_hero", "hero_type": "ARCHER"}))
        await ws2.recv()

        await ws1.send(json.dumps({"type": "start_game"}))
        await ws1.recv()
        await ws2.recv()
        print("Game setup complete")

        # Test pause
        print("Player 1 sending pause command...")
        await ws1.send(
            json.dumps({"type": "game_action", "action": {"type": "toggle_pause"}})
        )

        # Wait for game updates for both players
        print("Waiting for pause updates...")
        update1 = await wait_for_game_update(ws1)
        update2 = await wait_for_game_update(ws2)

        if update1 and update2:
            pause1 = update1.get("game_state", {}).get("is_paused", False)
            pause2 = update2.get("game_state", {}).get("is_paused", False)

            print(f"Player 1 sees paused: {pause1}")
            print(f"Player 2 sees paused: {pause2}")

            if pause1 and pause2:
                print("✅ Both players see the game is paused!")

                # Test unpause
                print("Player 2 sending unpause command...")
                await ws2.send(
                    json.dumps(
                        {"type": "game_action", "action": {"type": "toggle_pause"}}
                    )
                )

                print("Waiting for unpause updates...")
                update1 = await wait_for_game_update(ws1)
                update2 = await wait_for_game_update(ws2)

                if update1 and update2:
                    pause1 = update1.get("game_state", {}).get("is_paused", True)
                    pause2 = update2.get("game_state", {}).get("is_paused", True)

                    print(f"Player 1 sees paused: {pause1}")
                    print(f"Player 2 sees paused: {pause2}")

                    if not pause1 and not pause2:
                        print("✅ Both players see the game is unpaused!")
                    else:
                        print("❌ Unpause failed")
                else:
                    print("❌ Didn't receive unpause updates")
            else:
                print("❌ Pause failed")
        else:
            print("❌ Didn't receive pause updates")

        print("✅ Test completed!")


if __name__ == "__main__":
    asyncio.run(test_multiplayer_pause_robust())

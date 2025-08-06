#!/usr/bin/env python3

import asyncio
import json
import logging
import uuid

import websockets

logging.basicConfig(level=logging.INFO)


async def test_persistent_lobby():
    print("🎮 Testing Persistent Lobby Joining")
    print("===================================")

    # Client 1: Create lobby and stay connected
    client1_id = str(uuid.uuid4())
    client1_uri = f"ws://localhost:8000/ws/{client1_id}"

    print("1️⃣ Client 1 connecting and creating lobby...")

    try:
        async with websockets.connect(client1_uri) as websocket1:
            print("[Client 1] Connected!")

            # Create lobby
            create_message = {"type": "create_lobby", "player_name": "Player1"}
            await websocket1.send(json.dumps(create_message))

            # Wait for lobby creation response
            response = await websocket1.recv()
            data = json.loads(response)

            if data.get("type") == "lobby_created":
                lobby_id = data["lobby_id"]
                print(f"[Client 1] ✅ Lobby created: {lobby_id[:8]}...")

                # Keep this client connected and start client 2
                print("\n2️⃣ Client 2 attempting to join the same lobby...")

                # Client 2: Join the lobby
                client2_id = str(uuid.uuid4())
                client2_uri = f"ws://localhost:8000/ws/{client2_id}"

                try:
                    async with websockets.connect(client2_uri) as websocket2:
                        print("[Client 2] Connected!")

                        # Join lobby
                        join_message = {
                            "type": "join_lobby",
                            "lobby_id": lobby_id,
                            "player_name": "Player2",
                        }
                        await websocket2.send(json.dumps(join_message))

                        # Wait for join response
                        response2 = await websocket2.recv()
                        data2 = json.loads(response2)

                        print(f"[Client 2] Received: {data2}")

                        if data2.get("type") == "player_joined":
                            print("[Client 2] ✅ Successfully joined lobby!")
                            print(
                                f"[Client 2] Players in lobby: {data2.get('players', [])}"
                            )

                            # Client 1 should also receive the player_joined message
                            try:
                                response1 = await asyncio.wait_for(
                                    websocket1.recv(), timeout=2.0
                                )
                                data1 = json.loads(response1)
                                print(f"[Client 1] Received: {data1}")

                                if data1.get("type") == "player_joined":
                                    print("[Client 1] ✅ Notified of new player!")
                                    print(
                                        "🎉 SUCCESS: Both clients can join the same lobby!"
                                    )
                                else:
                                    print(f"[Client 1] ❌ Unexpected message: {data1}")
                            except asyncio.TimeoutError:
                                print(
                                    "[Client 1] ❌ Did not receive player_joined notification"
                                )

                        elif data2.get("type") == "join_failed":
                            print(
                                f"[Client 2] ❌ Join failed: {data2.get('reason', 'Unknown')}"
                            )
                            return False
                        else:
                            print(f"[Client 2] ❌ Unexpected response: {data2}")
                            return False

                        # Wait a bit to keep both connections active
                        await asyncio.sleep(1)

                except Exception as e:
                    print(f"[Client 2] ❌ Error: {e}")
                    return False

            else:
                print(f"[Client 1] ❌ Failed to create lobby: {data}")
                return False

    except Exception as e:
        print(f"[Client 1] ❌ Error: {e}")
        return False

    return True


if __name__ == "__main__":
    result = asyncio.run(test_persistent_lobby())
    if result:
        print("\n✅ Test passed!")
    else:
        print("\n❌ Test failed!")

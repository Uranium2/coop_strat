#!/usr/bin/env python3

import asyncio
import websockets
import json
import uuid
import time

async def test_client(client_id: int, action: str = "create"):
    player_id = str(uuid.uuid4())
    uri = f"ws://localhost:8000/ws/{player_id}"
    
    print(f"[Client {client_id}] Testing connection to {uri}")
    
    try:
        async with websockets.connect(uri) as websocket:
            print(f"[Client {client_id}] Connected successfully!")
            
            if action == "create":
                # Test lobby creation
                create_message = {
                    "type": "create_lobby",
                    "player_name": f"Player{client_id}"
                }
                
                print(f"[Client {client_id}] Creating lobby...")
                await websocket.send(json.dumps(create_message))
                
                response = await asyncio.wait_for(websocket.recv(), timeout=5)
                data = json.loads(response)
                
                if data.get("type") == "lobby_created":
                    lobby_id = data.get("lobby_id")
                    print(f"[Client {client_id}] ✅ Lobby created: {lobby_id}")
                    return lobby_id
                else:
                    print(f"[Client {client_id}] ❌ Unexpected response: {data}")
                    
            elif action == "list":
                # Test lobby listing
                list_message = {
                    "type": "list_lobbies"
                }
                
                print(f"[Client {client_id}] Requesting lobby list...")
                await websocket.send(json.dumps(list_message))
                
                response = await asyncio.wait_for(websocket.recv(), timeout=5)
                data = json.loads(response)
                
                if data.get("type") == "lobby_list":
                    lobbies = data.get("lobbies", [])
                    print(f"[Client {client_id}] ✅ Found {len(lobbies)} lobbies")
                    for lobby in lobbies:
                        print(f"[Client {client_id}]   - {lobby['lobby_id'][:8]}... ({lobby['player_count']}/{lobby['max_players']})")
                    return lobbies
                else:
                    print(f"[Client {client_id}] ❌ Unexpected response: {data}")
                    
            elif action.startswith("join:"):
                # Test joining specific lobby
                lobby_id = action.split(":")[1]
                join_message = {
                    "type": "join_lobby",
                    "lobby_id": lobby_id,
                    "player_name": f"Player{client_id}"
                }
                
                print(f"[Client {client_id}] Joining lobby {lobby_id[:8]}...")
                await websocket.send(json.dumps(join_message))
                
                response = await asyncio.wait_for(websocket.recv(), timeout=5)
                data = json.loads(response)
                
                if data.get("type") == "player_joined":
                    print(f"[Client {client_id}] ✅ Successfully joined lobby")
                    return True
                else:
                    print(f"[Client {client_id}] ❌ Failed to join: {data}")
                    return False
                    
    except Exception as e:
        print(f"[Client {client_id}] ❌ Connection failed: {e}")
        return None

async def test_multi_client():
    print("🎮 Testing Multi-Client Lobby System")
    print("=====================================")
    
    # Client 1: Create a lobby
    print("\n1️⃣ Testing lobby creation...")
    lobby_id = await test_client(1, "create")
    
    if not lobby_id:
        print("❌ Lobby creation failed, stopping test")
        return
    
    await asyncio.sleep(1)
    
    # Client 2: List lobbies
    print("\n2️⃣ Testing lobby listing...")
    lobbies = await test_client(2, "list")
    
    if not lobbies:
        print("❌ Lobby listing failed")
        return
    
    await asyncio.sleep(1)
    
    # Client 3: Join the lobby
    print("\n3️⃣ Testing lobby joining...")
    success = await test_client(3, f"join:{lobby_id}")
    
    if success:
        print("\n🎉 All tests passed! Multi-client lobby system working!")
    else:
        print("\n❌ Lobby joining failed")

if __name__ == "__main__":
    asyncio.run(test_multi_client())
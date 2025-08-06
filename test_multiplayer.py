#!/usr/bin/env python3
"""
Test script to verify multiplayer synchronization:
1. Creates a lobby with Player1
2. Player2 joins the lobby
3. Both players start the game
4. Verify they see the same map and each other
"""

import asyncio
import json
import time
from client.utils.network_manager import NetworkManager

class TestPlayer:
    def __init__(self, name):
        self.name = name
        self.nm = NetworkManager()
        self.lobby_id = None
        self.game_state = None
        
    async def connect(self):
        return await self.nm.connect()
    
    async def disconnect(self):
        await self.nm.disconnect()
    
    def register_handlers(self):
        self.nm.register_handler('lobby_created', self._on_lobby_created)
        self.nm.register_handler('player_joined', self._on_player_joined)
        self.nm.register_handler('game_started', self._on_game_started)
        self.nm.register_handler('game_update', self._on_game_update)
        
    def _on_lobby_created(self, data):
        print(f"{self.name}: Lobby created {data['lobby_id']}")
        self.lobby_id = data['lobby_id']
        
    def _on_player_joined(self, data):
        print(f"{self.name}: Player joined - {data['player_name']}")
        
    def _on_game_started(self, data):
        print(f"{self.name}: Game started!")
        self.game_state = data['game_state']
        print(f"{self.name}: Map size: {len(self.game_state['map_data'])}x{len(self.game_state['map_data'][0])}")
        print(f"{self.name}: Heroes: {list(self.game_state['heroes'].keys())}")
        print(f"{self.name}: Lobby ID in game state: {self.game_state.get('lobby_id', 'NOT FOUND')}")
        
    def _on_game_update(self, data):
        self.game_state = data['game_state']
        
    async def create_lobby(self):
        await self.nm.create_lobby(self.name)
        
    async def join_lobby(self, lobby_id):
        await self.nm.join_lobby(lobby_id, self.name)
        
    async def select_hero(self, hero_type="TANK"):
        await self.nm.select_hero(hero_type)
        
    async def start_game(self):
        await self.nm.start_game()

async def test_multiplayer():
    print("=== Testing Multiplayer Synchronization ===")
    
    # Create two test players
    player1 = TestPlayer("TestPlayer1")
    player2 = TestPlayer("TestPlayer2")
    
    # Register handlers
    player1.register_handlers()
    player2.register_handlers()
    
    try:
        # Connect both players
        print("\n1. Connecting players...")
        if not await player1.connect():
            print("Failed to connect Player1")
            return
        if not await player2.connect():
            print("Failed to connect Player2")
            return
        print("✓ Both players connected")
        
        # Player1 creates lobby
        print("\n2. Player1 creating lobby...")
        await player1.create_lobby()
        await asyncio.sleep(2)  # Wait for lobby creation
        
        if not player1.lobby_id:
            print("Failed to create lobby")
            return
        print(f"✓ Lobby created: {player1.lobby_id}")
        
        # Player2 joins lobby
        print("\n3. Player2 joining lobby...")
        await player2.join_lobby(player1.lobby_id)
        await asyncio.sleep(2)  # Wait for join
        print("✓ Player2 joined lobby")
        
        # Both players select heroes
        print("\n4. Selecting heroes...")
        await player1.select_hero("TANK")
        await player2.select_hero("ARCHER")
        await asyncio.sleep(1)
        print("✓ Heroes selected")
        
        # Start the game
        print("\n5. Starting game...")
        await player1.start_game()
        await asyncio.sleep(3)  # Wait for game to start
        
        # Check if both players received game state
        if not player1.game_state:
            print("❌ Player1 did not receive game state")
            return
        if not player2.game_state:
            print("❌ Player2 did not receive game state")
            return
            
        print("✓ Both players received game state")
        
        # Verify map synchronization
        print("\n6. Verifying map synchronization...")
        map1 = player1.game_state['map_data']
        map2 = player2.game_state['map_data']
        
        if map1 == map2:
            print("✓ Maps are identical!")
        else:
            print("❌ Maps are different!")
            print(f"Player1 map sample: {map1[0][:5] if map1 else 'None'}")
            print(f"Player2 map sample: {map2[0][:5] if map2 else 'None'}")
        
        # Verify heroes visibility
        print("\n7. Verifying player visibility...")
        heroes1 = player1.game_state['heroes']
        heroes2 = player2.game_state['heroes']
        
        if heroes1 == heroes2:
            print("✓ Both players see the same heroes!")
            print(f"Heroes count: {len(heroes1)}")
            for hero_id, hero in heroes1.items():
                player_id = hero['player_id']
                hero_type = hero['hero_type']
                position = hero['position']
                print(f"  Hero {hero_id[:8]}: Player {player_id[:8]} ({hero_type}) at ({position['x']}, {position['y']})")
        else:
            print("❌ Players see different heroes!")
            print(f"Player1 heroes: {len(heroes1)}")
            print(f"Player2 heroes: {len(heroes2)}")
        
        # Verify lobby ID is present
        print("\n8. Verifying lobby ID in game state...")
        lobby_id1 = player1.game_state.get('lobby_id')
        lobby_id2 = player2.game_state.get('lobby_id')
        
        if lobby_id1 and lobby_id2 and lobby_id1 == lobby_id2:
            print(f"✓ Lobby ID correctly included: {lobby_id1}")
        else:
            print(f"❌ Lobby ID issue - P1: {lobby_id1}, P2: {lobby_id2}")
            
        print("\n=== Test Complete ===")
        
    except Exception as e:
        print(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Disconnect players
        await player1.disconnect()
        await player2.disconnect()
        print("Players disconnected")

if __name__ == "__main__":
    asyncio.run(test_multiplayer())
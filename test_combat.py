#!/usr/bin/env python3
"""
Test script to verify enemy spawning and basic combat
"""

import asyncio
import time

from client.utils.network_manager import NetworkManager


class TestCombat:
    def __init__(self, name):
        self.name = name
        self.nm = NetworkManager()
        self.lobby_id = None
        self.game_state = None
        self.enemy_count = 0

    async def connect(self):
        return await self.nm.connect()

    async def disconnect(self):
        await self.nm.disconnect()

    def register_handlers(self):
        self.nm.register_handler("lobby_created", self._on_lobby_created)
        self.nm.register_handler("game_started", self._on_game_started)
        self.nm.register_handler("game_update", self._on_game_update)

    def _on_lobby_created(self, data):
        print(f"{self.name}: Lobby created {data['lobby_id']}")
        self.lobby_id = data["lobby_id"]

    def _on_game_started(self, data):
        print(f"{self.name}: Game started!")
        self.game_state = data["game_state"]
        print(f"{self.name}: Heroes: {len(self.game_state['heroes'])}")
        print(f"{self.name}: Initial enemies: {len(self.game_state['enemies'])}")

    def _on_game_update(self, data):
        self.game_state = data["game_state"]
        new_enemy_count = len(self.game_state["enemies"])
        if new_enemy_count != self.enemy_count:
            print(f"{self.name}: Enemy count changed: {self.enemy_count} -> {new_enemy_count}")
            self.enemy_count = new_enemy_count
            
            # List enemies and their positions
            for enemy_id, enemy in self.game_state["enemies"].items():
                if enemy["is_active"]:
                    pos = enemy["position"]
                    health = enemy["health"]
                    print(f"  Enemy {enemy_id[:8]}: Health {health} at ({pos['x']}, {pos['y']})")

    async def create_lobby(self):
        await self.nm.create_lobby(self.name)

    async def select_hero(self, hero_type="TANK"):
        await self.nm.select_hero(hero_type)

    async def start_game(self):
        await self.nm.start_game()

    async def attack_enemy(self, enemy_id):
        await self.nm.send_game_action({
            "type": "attack_enemy", 
            "enemy_id": enemy_id
        })


async def test_combat():
    print("=== Testing Enemy Spawning and Combat ===")
    
    player = TestCombat("TestPlayer")
    player.register_handlers()
    
    try:
        # Connect and create lobby
        print("\n1. Connecting and creating lobby...")
        if not await player.connect():
            print("Failed to connect")
            return
        
        await player.create_lobby()
        await asyncio.sleep(1)
        
        if not player.lobby_id:
            print("Failed to create lobby")
            return
        print(f"✓ Lobby created: {player.lobby_id}")
        
        # Select hero and start game
        print("\n2. Starting game...")
        await player.select_hero("TANK")
        await asyncio.sleep(0.5)
        await player.start_game()
        await asyncio.sleep(2)
        
        if not player.game_state:
            print("Failed to start game")
            return
        print("✓ Game started successfully")
        
        # Wait for enemies to spawn (10 seconds)
        print("\n3. Waiting for enemies to spawn...")
        for i in range(15):
            await asyncio.sleep(1)
            print(f"  Waiting {i+1}/15 seconds...")
            if player.enemy_count > 0:
                print(f"✓ Enemies spawned! Count: {player.enemy_count}")
                break
        
        if player.enemy_count == 0:
            print("❌ No enemies spawned after 15 seconds")
            return
        
        # Test combat by moving hero close to enemy
        print("\n4. Testing combat...")
        enemies = player.game_state["enemies"]
        if enemies:
            # Get first active enemy
            target_enemy = None
            for enemy_id, enemy in enemies.items():
                if enemy["is_active"] and enemy["health"] > 0:
                    target_enemy = enemy_id
                    break
            
            if target_enemy:
                enemy = player.game_state["enemies"][target_enemy]
                enemy_pos = enemy["position"]
                
                # Get hero position before moving
                hero = list(player.game_state["heroes"].values())[0]
                hero_pos = hero["position"]
                print(f"Hero position before: ({hero_pos['x']}, {hero_pos['y']})")
                print(f"Moving hero to enemy at ({enemy_pos['x']}, {enemy_pos['y']})...")
                
                # Move hero close to enemy to trigger combat
                await player.nm.send_game_action({
                    "type": "move_hero",
                    "target_position": {"x": enemy_pos["x"], "y": enemy_pos["y"]}
                })
                
                # Wait for combat to process (much longer wait for full movement)
                print("Waiting for hero to reach enemy...")
                for i in range(20):  # Wait up to 20 seconds
                    await asyncio.sleep(1)
                    hero = list(player.game_state["heroes"].values())[0]
                    hero_pos = hero["position"]
                    distance = ((hero_pos["x"] - enemy_pos["x"])**2 + (hero_pos["y"] - enemy_pos["y"])**2)**0.5
                    print(f"  {i+1}s: Hero at ({hero_pos['x']:.1f}, {hero_pos['y']:.1f}), distance to enemy: {distance:.1f}")
                    if distance < 2.0:  # Close enough for combat
                        print("  Hero reached combat range!")
                        await asyncio.sleep(2)  # Wait for combat to process
                        break
                
                # Check final positions and combat result
                hero = list(player.game_state["heroes"].values())[0]
                hero_pos = hero["position"]
                print(f"Hero position after: ({hero_pos['x']}, {hero_pos['y']})")
                
                # Check if enemy took damage
                enemy = player.game_state["enemies"][target_enemy]
                print(f"Enemy health after moving close: {enemy['health']}")
                if enemy['health'] < enemy['max_health']:
                    print("✓ Combat working! Enemy took damage")
                else:
                    print("❌ Enemy didn't take damage")
            else:
                print("❌ No active enemies to attack")
        
        print("\n=== Test Complete ===")
        
    except Exception as e:
        print(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await player.disconnect()


if __name__ == "__main__":
    asyncio.run(test_combat())
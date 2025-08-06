#!/usr/bin/env python3
"""
Test script to verify that active games show up in lobby browser
"""

import asyncio

from client.utils.network_manager import NetworkManager


async def test_active_game_visibility():
    print("=== Testing Active Game Lobby Visibility ===")

    # Create test players
    player1 = NetworkManager()
    player2 = NetworkManager()
    browser = NetworkManager()

    # Register basic handlers
    lobby_id = None

    def on_lobby_created(data):
        nonlocal lobby_id
        lobby_id = data["lobby_id"]
        print(f"Lobby created: {lobby_id}")

    def on_game_started(data):
        print("Game started successfully!")

    def on_lobby_list(data):
        lobbies = data.get("lobbies", [])
        print(f"\nLobby Browser Results ({len(lobbies)} lobbies):")
        for lobby in lobbies:
            status = lobby.get("status", "unknown")
            players = lobby.get("player_count", 0)
            max_players = lobby.get("max_players", 4)
            lobby_id_short = lobby["lobby_id"][:12] + "..."
            print(
                f"  {lobby_id_short} - {players}/{max_players} players - Status: {status}"
            )

    player1.register_handler("lobby_created", on_lobby_created)
    player1.register_handler("game_started", on_game_started)
    player2.register_handler("game_started", on_game_started)
    browser.register_handler("lobby_list", on_lobby_list)

    try:
        # Step 1: Connect all players
        print("\n1. Connecting players...")
        await player1.connect()
        await player2.connect()
        await browser.connect()
        print("✓ All players connected")

        # Step 2: Create lobby
        print("\n2. Creating lobby...")
        await player1.create_lobby("Player1")
        await asyncio.sleep(2)

        # Step 3: Join lobby
        print("\n3. Player2 joining lobby...")
        await player2.join_lobby(lobby_id, "Player2")
        await asyncio.sleep(1)

        # Step 4: Check lobby browser BEFORE game starts
        print("\n4. Checking lobby browser BEFORE game starts...")
        await browser.list_lobbies()
        await asyncio.sleep(1)

        # Step 5: Select heroes and start game
        print("\n5. Starting game...")
        await player1.select_hero("TANK")
        await player2.select_hero("ARCHER")
        await asyncio.sleep(1)
        await player1.start_game()
        await asyncio.sleep(3)  # Wait for game to start

        # Step 6: Check lobby browser AFTER game starts
        print("\n6. Checking lobby browser AFTER game starts...")
        await browser.list_lobbies()
        await asyncio.sleep(1)

        # Step 7: Disconnect players (simulating leaving during game)
        print("\n7. Players disconnecting from active game...")
        await player1.disconnect()
        await player2.disconnect()
        await asyncio.sleep(2)

        # Step 8: Check lobby browser AFTER players disconnect
        print("\n8. Checking lobby browser AFTER players disconnect...")
        await browser.list_lobbies()
        await asyncio.sleep(1)

        print("\n=== Test Complete ===")

    except Exception as e:
        print(f"Test failed: {e}")
        import traceback

        traceback.print_exc()
    finally:
        # Cleanup
        try:
            await player1.disconnect()
            await player2.disconnect()
            await browser.disconnect()
        except Exception as e:
            print(f"Error during cleanup: {e}")


if __name__ == "__main__":
    asyncio.run(test_active_game_visibility())

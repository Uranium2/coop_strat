#!/usr/bin/env python3

import asyncio
import os
import sys

import pygame

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from client.scenes.game_scene import GameScene
from shared.constants.game_constants import TILE_SIZE
from shared.models.game_models import (
    BuildingType,
    GameState,
    Hero,
    HeroType,
    Player,
    Position,
    Resources,
)


class MockNetworkManager:
    def __init__(self):
        self.player_id = "test_player"
        self.actions_sent = []

    async def send_game_action(self, action):
        self.actions_sent.append(action)
        print(f"🌐 Action Sent: {action}")


def create_test_game_state():
    """Create a test game state"""
    player = Player(
        id="test_player",
        name="Test Player",
        hero_type=HeroType.WARRIOR,
        resources=Resources(wood=100, stone=50, gold=100),
    )

    # Hero starts at (5, 5) * 32 = (160, 160)
    hero = Hero(
        id="hero_1",
        player_id="test_player",
        hero_type=HeroType.WARRIOR,
        position=Position(x=160, y=160),
        health=100,
        max_health=100,
        attack_damage=25,
        attack_range=1.5,
    )

    map_data = [["GRASS" for _ in range(20)] for _ in range(20)]
    fog_of_war = [[True for _ in range(20)] for _ in range(20)]

    game_state = GameState(
        players={"test_player": player},
        heroes={"hero_1": hero},
        units={},
        buildings={},
        enemies={},
        map_data=map_data,
        fog_of_war=fog_of_war,
        wave_number=1,
        is_active=True,
        is_paused=False,
        game_time=0.0,
    )

    return game_state


def debug_building_workflow():
    """Debug the complete building workflow step by step"""
    print("🔍 Debugging Building Workflow - Hero Arrival Detection")
    print("=" * 70)

    # Setup
    pygame.init()
    screen = pygame.display.set_mode((800, 600))

    network_manager = MockNetworkManager()
    initial_game_state = create_test_game_state()
    game_scene = GameScene(screen, network_manager, initial_game_state)
    game_scene.game_state = initial_game_state

    building_placer = game_scene.building_placer

    print("\n📍 Step 1: Initial Setup")
    hero = game_scene._get_player_hero()
    print(f"   Hero position: ({hero.position.x}, {hero.position.y})")
    print(
        f"   Building placer state: placing={building_placer.is_placing()}, map_preview={building_placer.has_map_preview()}"
    )

    print("\n📍 Step 2: Start Building Placement")
    building_placer.start_placement(BuildingType.BARRACKS)
    print(f"   Building placement started: {building_placer.is_placing()}")
    print(f"   Cursor preview mode: {building_placer.is_cursor_preview}")

    print("\n📍 Step 3: Place Preview on Map")
    # Place at (15, 15) tiles = (480, 480) pixels
    target_position = Position(x=480, y=480)
    placement_result = building_placer.place_preview_on_map(
        target_position, game_scene.game_state, network_manager.player_id
    )
    print(f"   Placement successful: {placement_result}")
    print(f"   Map preview exists: {building_placer.has_map_preview()}")
    print(f"   Cursor preview mode: {building_placer.is_cursor_preview}")

    preview_info = building_placer.get_map_preview_info()
    if preview_info:
        building_type, position = preview_info
        print(f"   Preview building: {building_type.value}")
        print(f"   Preview position: ({position.x}, {position.y})")

        print("\n📍 Step 4: Check Hero Proximity")
        is_adjacent = building_placer._is_hero_adjacent_to_building(hero, position)
        print(f"   Hero adjacent to build location: {is_adjacent}")
        if not is_adjacent:
            distance = (
                (hero.position.x - position.x) ** 2
                + (hero.position.y - position.y) ** 2
            ) ** 0.5
            print(
                f"   Distance: {distance:.2f} pixels, {distance / TILE_SIZE:.2f} tiles"
            )

    print("\n📍 Step 5: Simulate Game Scene Click Logic")
    # Simulate the click handling that happens in game scene
    world_pos = Position(x=480, y=480)

    # This simulates the game scene logic
    if building_placer.place_preview_on_map(
        world_pos, game_scene.game_state, network_manager.player_id
    ):
        game_scene.building_menu.clear_selection()

        preview_info = building_placer.get_map_preview_info()
        if preview_info:
            building_type, position = preview_info
            hero = game_scene._get_player_hero()

            if hero and not building_placer._is_hero_adjacent_to_building(
                hero, position
            ):
                print("   🏃 Hero needs to travel - sending move command")
                target_x = position.x / TILE_SIZE
                target_y = position.y / TILE_SIZE

                # This would be sent to server
                move_action = {
                    "type": "move_hero",
                    "target_position": {"x": target_x, "y": target_y},
                }

                building_placer.set_hero_traveling(True)
                game_scene.pending_build = {
                    "building_type": building_type.value,
                    "position": {"x": int(target_x), "y": int(target_y)},
                }

                print(f"   Move action: {move_action}")
                print(
                    f"   Hero traveling state: {building_placer.hero_traveling_to_build}"
                )
                print(f"   Pending build: {game_scene.pending_build}")
            else:
                print("   ✅ Hero already adjacent - would build immediately")

    print("\n📍 Step 6: Simulate Hero Movement")
    # Move hero step by step towards target
    target_pos = Position(x=480, y=480)
    original_pos = Position(x=hero.position.x, y=hero.position.y)

    # Calculate movement steps
    dx = target_pos.x - original_pos.x
    dy = target_pos.y - original_pos.y
    distance = (dx**2 + dy**2) ** 0.5
    steps = int(distance / 10)  # Move in steps of 10 pixels

    print(
        f"   Moving hero from ({original_pos.x}, {original_pos.y}) to ({target_pos.x}, {target_pos.y})"
    )
    print(f"   Total distance: {distance:.2f} pixels, {steps} steps")

    for step in range(steps + 1):
        progress = step / steps if steps > 0 else 1.0
        new_x = original_pos.x + dx * progress
        new_y = original_pos.y + dy * progress
        hero.position = Position(x=new_x, y=new_y)

        # Check proximity at each step
        is_adjacent = building_placer._is_hero_adjacent_to_building(hero, target_pos)
        remaining_distance = (
            (hero.position.x - target_pos.x) ** 2
            + (hero.position.y - target_pos.y) ** 2
        ) ** 0.5

        print(
            f"   Step {step}: pos=({new_x:.1f}, {new_y:.1f}), distance={remaining_distance:.1f}, adjacent={is_adjacent}"
        )

        # Simulate the update logic that checks for hero arrival
        if (
            game_scene.pending_build
            and building_placer.hero_traveling_to_build
            and building_placer.has_map_preview()
        ):
            preview_info = building_placer.get_map_preview_info()
            if preview_info:
                building_type, position = preview_info
                if building_placer._is_hero_adjacent_to_building(hero, position):
                    print("   🎉 HERO ARRIVED! Building should be constructed now!")
                    print(f"   Build action would be sent: {game_scene.pending_build}")

                    # This is what should happen
                    building_placer.clear_map_preview()
                    game_scene.pending_build = None
                    building_placer.set_hero_traveling(False)
                    print("   ✅ Building workflow completed!")
                    break

    print("\n📍 Step 7: Final State Check")
    print(f"   Hero final position: ({hero.position.x}, {hero.position.y})")
    print(f"   Map preview exists: {building_placer.has_map_preview()}")
    print(f"   Hero traveling: {building_placer.hero_traveling_to_build}")
    print(f"   Pending build: {game_scene.pending_build}")

    pygame.quit()
    return True


async def main():
    """Run the debug session"""
    try:
        debug_building_workflow()
        print("\n" + "=" * 70)
        print("🔍 Debug session completed!")
        print("=" * 70)

    except Exception as e:
        print(f"\n❌ Debug failed with error: {e}")
        import traceback

        traceback.print_exc()
        raise


if __name__ == "__main__":
    asyncio.run(main())

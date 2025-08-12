#!/usr/bin/env python3

import asyncio
import os
import sys
import time

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import pygame

from client.scenes.game_scene import GameScene
from shared.constants.game_constants import FPS, SCREEN_HEIGHT, SCREEN_WIDTH
from shared.models.game_models import (
    BuildingType,
    Hero,
    HeroType,
    Player,
    Position,
    Resources,
)


class TestHeroTravelToBuild:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Test Hero Travel to Build")
        self.clock = pygame.time.Clock()

        # Create mock game state
        self.player_id = "test_player"
        self.hero = Hero(
            id="hero_1",
            player_id=self.player_id,
            hero_type=HeroType.BUILDER,
            position=Position(x=10, y=10),  # Start hero away from build location
            health=100,
            max_health=100,
        )

        self.player = Player(
            id=self.player_id,
            name="Test Player",
            hero_type=HeroType.BUILDER,
            resources=Resources(wood=100, stone=100, wheat=100, metal=100, gold=100),
        )

        # Create initial game state
        initial_state = {
            "players": {self.player_id: self.player.dict()},
            "heroes": {"hero_1": self.hero.dict()},
            "buildings": {},
            "units": {},
            "enemies": {},
            "pings": {},
            "attack_effects": {},
            "map_data": [["EMPTY" for _ in range(50)] for _ in range(50)],
            "fog_of_war": [[True for _ in range(50)] for _ in range(50)],
            "game_time": 0.0,
            "is_active": True,
            "is_paused": False,
            "game_over_reason": "NONE",
            "wave_number": 0,
            "next_wave_time": 60.0,
            "time_to_next_wave": 60.0,
        }

        # Mock network manager
        self.network_manager = MockNetworkManager(self.player_id)

        # Create game scene
        self.game_scene = GameScene(self.screen, self.network_manager, initial_state)

        # Test state tracking
        self.test_phase = "start"
        self.build_location = Position(x=15 * 32, y=15 * 32)  # 5 tiles away from hero
        self.test_start_time = time.time()

    async def run_test(self):
        """Run the complete hero travel-to-build test"""
        print("🏗️  Starting Hero Travel-to-Build Test")
        print("=" * 50)

        running = True
        test_phase = "initial"
        phase_start_time = time.time()

        # Test phases
        phase_times = {
            "initial": 2.0,  # Show initial state
            "start_build": 1.0,  # Start building placement
            "click_far": 1.0,  # Click far from hero - should show orange
            "wait_travel": 5.0,  # Wait for hero to travel
            "verify_build": 2.0,  # Verify building was created
        }

        while running:
            current_time = time.time()
            dt = self.clock.tick(FPS) / 1000.0

            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_SPACE:
                        # Manual advance to next phase
                        test_phase = self._advance_test_phase(test_phase)
                        phase_start_time = current_time

                # Let game scene handle events for building placement
                self.game_scene.handle_event(event)

            # Auto-advance test phases
            phase_elapsed = current_time - phase_start_time
            if phase_elapsed >= phase_times.get(test_phase, 10.0):
                new_phase = self._advance_test_phase(test_phase)
                if new_phase != test_phase:
                    test_phase = new_phase
                    phase_start_time = current_time
                    print(f"📍 Test Phase: {test_phase}")

            # Execute test logic based on phase
            await self._execute_test_phase(test_phase, phase_elapsed)

            # Update game scene
            self.game_scene.update(dt)

            # Render
            self.game_scene.render(self.screen)

            # Draw test overlay
            self._draw_test_overlay(
                test_phase, phase_elapsed, phase_times.get(test_phase, 10.0)
            )

            pygame.display.flip()

            # Check for test completion
            if test_phase == "complete":
                await asyncio.sleep(2.0)
                break

        print("\n✅ Hero Travel-to-Build Test Complete!")
        pygame.quit()

    def _advance_test_phase(self, current_phase):
        """Advance to the next test phase"""
        phases = [
            "initial",
            "start_build",
            "click_far",
            "wait_travel",
            "verify_build",
            "complete",
        ]
        try:
            current_idx = phases.index(current_phase)
            if current_idx < len(phases) - 1:
                return phases[current_idx + 1]
        except ValueError:
            pass
        return "complete"

    async def _execute_test_phase(self, phase, elapsed):
        """Execute logic for current test phase"""
        if phase == "start_build":
            if elapsed < 0.5:  # Only do this once at start of phase
                # Select hero and open building menu
                hero = self.game_scene._get_player_hero()
                if hero:
                    self.game_scene.selected_entity = hero
                    self.game_scene.building_menu.show(
                        self.game_scene.game_state.players[self.player_id].resources
                    )
                    # Start wall building placement
                    self.game_scene.building_placer.start_placement(BuildingType.WALL)
                    print("🔨 Started building placement mode")

        elif phase == "click_far":
            if elapsed < 0.5:  # Only do this once at start of phase
                # Simulate clicking far from hero to trigger travel
                mouse_pos = (
                    self.build_location.x - self.game_scene.camera_x,
                    self.build_location.y - self.game_scene.camera_y,
                )

                # Create a mock mouse click event
                click_event = pygame.event.Event(
                    pygame.MOUSEBUTTONDOWN, button=1, pos=mouse_pos
                )
                self.game_scene.handle_event(click_event)
                print(
                    f"🖱️  Clicked far from hero at {self.build_location.x}, {self.build_location.y}"
                )

        elif phase == "wait_travel":
            # Check if hero has moved closer to build location
            hero = self.game_scene._get_player_hero()
            if hero:
                distance = (
                    (hero.position.x - self.build_location.x / 32) ** 2
                    + (hero.position.y - self.build_location.y / 32) ** 2
                ) ** 0.5
                if distance <= 2.0:  # Hero reached destination
                    print(f"🎯 Hero reached build location! Distance: {distance:.1f}")
                    return "verify_build"

        elif phase == "verify_build":
            # Check if building was created
            if self.game_scene.game_state.buildings:
                print("🏗️  Building successfully created!")
                return "complete"

    def _draw_test_overlay(self, phase, elapsed, total_time):
        """Draw test status overlay"""
        font = pygame.font.Font(None, 36)
        small_font = pygame.font.Font(None, 24)

        # Draw test title
        title = font.render("Hero Travel-to-Build Test", True, (255, 255, 255))
        self.screen.blit(title, (10, 10))

        # Draw current phase
        phase_text = f"Phase: {phase.replace('_', ' ').title()}"
        phase_surface = small_font.render(phase_text, True, (255, 255, 0))
        self.screen.blit(phase_surface, (10, 50))

        # Draw progress bar
        progress = min(elapsed / total_time, 1.0)
        bar_width = 300
        bar_height = 20
        bar_x, bar_y = 10, 80

        # Background
        pygame.draw.rect(
            self.screen, (64, 64, 64), (bar_x, bar_y, bar_width, bar_height)
        )
        # Progress
        pygame.draw.rect(
            self.screen,
            (0, 255, 0),
            (bar_x, bar_y, int(bar_width * progress), bar_height),
        )
        # Border
        pygame.draw.rect(
            self.screen, (255, 255, 255), (bar_x, bar_y, bar_width, bar_height), 2
        )

        # Draw hero position
        hero = self.game_scene._get_player_hero()
        if hero:
            pos_text = f"Hero: ({hero.position.x:.1f}, {hero.position.y:.1f})"
            pos_surface = small_font.render(pos_text, True, (0, 255, 255))
            self.screen.blit(pos_surface, (10, 110))

        # Draw building placer state
        if self.game_scene.building_placer.is_placing():
            state_text = (
                f"Build State: {self.game_scene.building_placer.preview_state.value}"
            )
            state_color = {
                "VALID": (0, 255, 0),
                "TRAVELING": (255, 165, 0),
                "INVALID": (255, 0, 0),
            }.get(self.game_scene.building_placer.preview_state.value, (255, 255, 255))

            state_surface = small_font.render(state_text, True, state_color)
            self.screen.blit(state_surface, (10, 140))

        # Draw instructions
        instructions = [
            "Instructions:",
            "- Watch hero travel to build location",
            "- Preview should turn ORANGE while traveling",
            "- Building should auto-place when hero arrives",
            "- Press SPACE to advance phases manually",
            "- Press ESC to exit",
        ]

        for i, instruction in enumerate(instructions):
            color = (255, 255, 255) if i == 0 else (200, 200, 200)
            instr_surface = small_font.render(instruction, True, color)
            self.screen.blit(instr_surface, (10, 170 + i * 25))


class MockNetworkManager:
    def __init__(self, player_id):
        self.player_id = player_id
        self.handlers = {}

    def register_handler(self, event_type, handler):
        self.handlers[event_type] = handler

    async def send_game_action(self, action):
        """Mock sending game actions - just print what would be sent"""
        print(f"🌐 Mock Network Action: {action}")

        # Simulate hero movement response
        if action.get("type") == "move_hero":
            # Mock hero reaching destination after short delay
            await asyncio.sleep(0.1)
            print("🏃 Hero movement started")

        elif action.get("type") == "build":
            # Mock successful building
            await asyncio.sleep(0.1)
            print(f"🏗️  Building {action.get('building_type')} placed!")


async def main():
    test = TestHeroTravelToBuild()
    await test.run_test()


if __name__ == "__main__":
    asyncio.run(main())

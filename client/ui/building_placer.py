import math
from typing import Optional, Tuple

import pygame

from shared.constants.game_constants import BUILDING_TYPES, COLORS, TILE_SIZE
from shared.models.game_models import BuildingPreviewState, BuildingType, Position


class BuildingPlacer:
    def __init__(self):
        self.building_type: Optional[BuildingType] = None
        self.preview_position: Optional[Position] = None
        self.preview_state = BuildingPreviewState.INVALID
        self.hero_traveling_to_build = (
            False  # Track if hero is moving to build location
        )
        self.placed_preview_position: Optional[Position] = None  # Fixed position on map
        self.placed_preview_type: Optional[BuildingType] = (
            None  # Type of placed preview
        )
        self.is_cursor_preview = (
            True  # Whether preview follows cursor or is placed on map
        )

    def start_placement(self, building_type: BuildingType):
        """Start placing a building"""
        self.building_type = building_type
        self.preview_position = None
        self.preview_state = BuildingPreviewState.INVALID
        self.hero_traveling_to_build = False
        self.placed_preview_position = None
        self.placed_preview_type = None
        self.is_cursor_preview = True

    def stop_placement(self):
        """Stop placing a building"""
        self.building_type = None
        self.preview_position = None
        self.preview_state = BuildingPreviewState.INVALID
        self.hero_traveling_to_build = False
        self.placed_preview_position = None
        self.placed_preview_type = None
        self.is_cursor_preview = True

    def place_preview_on_map(self, world_pos: Position, game_state, player_id: str):
        """Place the building preview at a fixed position on the map"""
        if not self.building_type:
            return False

        # Snap to grid
        grid_x = int(world_pos.x // TILE_SIZE) * TILE_SIZE
        grid_y = int(world_pos.y // TILE_SIZE) * TILE_SIZE
        placement_position = Position(x=grid_x, y=grid_y)

        # Check if placement is valid at this location
        preview_state = self._determine_preview_state(
            placement_position, game_state, player_id
        )
        if preview_state == BuildingPreviewState.INVALID:
            return False

        # Place the preview on the map
        self.placed_preview_position = placement_position
        self.placed_preview_type = self.building_type
        self.is_cursor_preview = False

        # Update hero traveling state if needed
        if preview_state == BuildingPreviewState.TRAVELING:
            self.hero_traveling_to_build = False  # Will be set by game scene

        return True

    def clear_map_preview(self):
        """Clear the placed preview from the map"""
        self.placed_preview_position = None
        self.placed_preview_type = None
        self.is_cursor_preview = True
        self.hero_traveling_to_build = False

    def has_map_preview(self) -> bool:
        """Check if there's a preview placed on the map"""
        return (
            self.placed_preview_position is not None
            and self.placed_preview_type is not None
        )

    def get_map_preview_info(self) -> Optional[Tuple[BuildingType, Position]]:
        """Get map preview info"""
        if (
            self.has_map_preview()
            and self.placed_preview_type
            and self.placed_preview_position
        ):
            return (self.placed_preview_type, self.placed_preview_position)
        return None

    def set_hero_traveling(self, traveling: bool):
        """Set whether hero is traveling to build location"""
        self.hero_traveling_to_build = traveling

    def update_position(self, world_pos: Position, game_state, player_id: str):
        """Update the preview position and check validity"""
        if not self.building_type:
            return

        # Snap to grid
        grid_x = int(world_pos.x // TILE_SIZE) * TILE_SIZE
        grid_y = int(world_pos.y // TILE_SIZE) * TILE_SIZE
        self.preview_position = Position(x=grid_x, y=grid_y)

        # Check placement validity and hero proximity
        self.preview_state = self._determine_preview_state(
            self.preview_position, game_state, player_id
        )

    def _determine_preview_state(
        self, position: Position, game_state, player_id: str
    ) -> BuildingPreviewState:
        """Determine the preview state based on placement validity and hero proximity"""
        if not self.building_type or not position:
            return BuildingPreviewState.INVALID

        # First check basic placement validity
        if not self._check_placement_validity(position, game_state, player_id):
            return BuildingPreviewState.INVALID

        # Check hero proximity
        hero = self._get_player_hero(game_state, player_id)
        if not hero:
            return BuildingPreviewState.INVALID

        # Check if hero is adjacent to the building position
        if self._is_hero_adjacent_to_building(hero, position):
            return BuildingPreviewState.VALID
        elif self.hero_traveling_to_build:
            return BuildingPreviewState.TRAVELING
        else:
            return BuildingPreviewState.TRAVELING  # Will trigger hero movement

    def _get_player_hero(self, game_state, player_id: str):
        """Get the player's hero"""
        for hero in game_state.heroes.values():
            if hero.player_id == player_id:
                return hero
        return None

    def _is_hero_adjacent_to_building(self, hero, building_position: Position) -> bool:
        """Check if hero is adjacent to the building position"""
        if not self.building_type:
            return False

        building_info = BUILDING_TYPES.get(self.building_type.value)
        if not building_info:
            return False

        size = building_info["size"]

        # Convert to tile coordinates
        # Hero position is already in tile coordinates
        hero_tile_x = hero.position.x
        hero_tile_y = hero.position.y
        # Building position is in pixel coordinates, convert to tiles
        building_tile_x = building_position.x // TILE_SIZE
        building_tile_y = building_position.y // TILE_SIZE

        # Check if hero is adjacent to any part of the building
        # Hero needs to be within 1.5 tiles of the building's edge (allows diagonal adjacency)
        for bx in range(int(building_tile_x), int(building_tile_x) + size[0]):
            for by in range(int(building_tile_y), int(building_tile_y) + size[1]):
                distance = math.sqrt((hero_tile_x - bx) ** 2 + (hero_tile_y - by) ** 2)
                if distance <= 1.8:  # Slightly more lenient to match server threshold
                    return True

        # Debug info
        min_distance = float("inf")
        for bx in range(int(building_tile_x), int(building_tile_x) + size[0]):
            for by in range(int(building_tile_y), int(building_tile_y) + size[1]):
                distance = math.sqrt((hero_tile_x - bx) ** 2 + (hero_tile_y - by) ** 2)
                min_distance = min(min_distance, distance)

        # Uncomment for debugging
        # print(f"🔍 Hero at tile ({hero_tile_x:.2f}, {hero_tile_y:.2f}), building at ({building_tile_x:.2f}, {building_tile_y:.2f}), min distance: {min_distance:.2f}")

        return False

    def _check_placement_validity(
        self, position: Position, game_state, player_id: str
    ) -> bool:
        """Check if the building can be placed at the given position"""
        if not self.building_type or not position:
            return False

        building_info = BUILDING_TYPES.get(self.building_type.value)
        if not building_info:
            return False

        size = building_info["size"]

        # Check bounds
        if (
            position.x < 0
            or position.y < 0
            or position.x + size[0] * TILE_SIZE
            > len(game_state.map_data[0]) * TILE_SIZE
            or position.y + size[1] * TILE_SIZE > len(game_state.map_data) * TILE_SIZE
        ):
            return False

        # Check fog of war - all tiles must be explored
        building_start_x = int(position.x // TILE_SIZE)
        building_start_y = int(position.y // TILE_SIZE)
        building_end_x = building_start_x + size[0]
        building_end_y = building_start_y + size[1]

        if hasattr(game_state, "fog_of_war") and game_state.fog_of_war:
            for tile_y in range(building_start_y, building_end_y):
                for tile_x in range(building_start_x, building_end_x):
                    if (
                        tile_y >= len(game_state.fog_of_war)
                        or tile_x >= len(game_state.fog_of_war[0])
                        or not game_state.fog_of_war[tile_y][tile_x]
                    ):
                        return False  # Cannot build in unexplored areas

        # Check for overlapping buildings
        for building in game_state.buildings.values():
            if self._buildings_overlap(
                position, size, building.position, building.size
            ):
                return False

        # Check for overlapping heroes (except builder)
        for hero in game_state.heroes.values():
            if (
                hero.player_id != player_id
            ):  # Allow builder to place on their own position
                hero_tile_x = int(hero.position.x // TILE_SIZE)
                hero_tile_y = int(hero.position.y // TILE_SIZE)

                if (
                    building_start_x <= hero_tile_x < building_end_x
                    and building_start_y <= hero_tile_y < building_end_y
                ):
                    return False

        # Check for overlapping units
        for unit in game_state.units.values():
            unit_tile_x = int(unit.position.x // TILE_SIZE)
            unit_tile_y = int(unit.position.y // TILE_SIZE)

            if (
                building_start_x <= unit_tile_x < building_end_x
                and building_start_y <= unit_tile_y < building_end_y
            ):
                return False

        return True

    def _buildings_overlap(
        self,
        pos1: Position,
        size1: Tuple[int, int],
        pos2: Position,
        size2: Tuple[int, int],
    ) -> bool:
        """Check if two buildings overlap"""
        # Convert positions to tile coordinates
        x1, y1 = int(pos1.x // TILE_SIZE), int(pos1.y // TILE_SIZE)
        x2, y2 = int(pos2.x // TILE_SIZE), int(pos2.y // TILE_SIZE)

        # Check overlap using proper rectangle collision detection
        # Building 1: from (x1, y1) to (x1 + size1[0], y1 + size1[1])
        # Building 2: from (x2, y2) to (x2 + size2[0], y2 + size2[1])
        return not (
            x1 + size1[0] <= x2
            or x2 + size2[0] <= x1
            or y1 + size1[1] <= y2
            or y2 + size2[1] <= y1
        )

    def get_placement_info(self) -> Optional[Tuple[BuildingType, Position, bool]]:
        """Get current placement info"""
        if self.building_type and self.preview_position:
            is_valid = self.preview_state == BuildingPreviewState.VALID
            return (self.building_type, self.preview_position, is_valid)
        return None

    def render_preview(self, screen: pygame.Surface, camera_offset: Tuple[int, int]):
        """Render the building placement preview"""
        # Render cursor preview (follows mouse)
        if self.is_cursor_preview and self.building_type and self.preview_position:
            self._render_building_preview(
                screen,
                camera_offset,
                self.building_type,
                self.preview_position,
                self.preview_state,
            )

        # Render map preview (fixed position) - basic rendering without state update
        if (
            self.has_map_preview()
            and self.placed_preview_type
            and self.placed_preview_position
        ):
            # Use a default state for basic rendering when game state is not available
            self._render_building_preview(
                screen,
                camera_offset,
                self.placed_preview_type,
                self.placed_preview_position,
                BuildingPreviewState.TRAVELING,
            )

    def render_map_preview(
        self,
        screen: pygame.Surface,
        camera_offset: Tuple[int, int],
        game_state,
        player_id: str,
    ):
        """Render only the map-placed building preview with current state"""
        if (
            not self.has_map_preview()
            or not self.placed_preview_type
            or not self.placed_preview_position
        ):
            return

        # Determine current preview state
        map_preview_state = self._determine_preview_state(
            self.placed_preview_position, game_state, player_id
        )

        self._render_building_preview(
            screen,
            camera_offset,
            self.placed_preview_type,
            self.placed_preview_position,
            map_preview_state,
        )

    def _render_building_preview(
        self,
        screen: pygame.Surface,
        camera_offset: Tuple[int, int],
        building_type: BuildingType,
        position: Position,
        state: BuildingPreviewState,
    ):
        """Render a building preview at the given position"""
        building_info = BUILDING_TYPES.get(building_type.value)
        if not building_info:
            return

        size = building_info["size"]

        # Calculate screen position
        screen_x = position.x - camera_offset[0]
        screen_y = position.y - camera_offset[1]

        # Building preview rectangle
        preview_rect = pygame.Rect(
            screen_x, screen_y, size[0] * TILE_SIZE, size[1] * TILE_SIZE
        )

        # Choose color based on preview state
        if state == BuildingPreviewState.VALID:
            color = (*COLORS["GREEN"][:3], 128)  # Semi-transparent green
            border_color = COLORS["GREEN"]
            status_text = "Ready to Build"
        elif state == BuildingPreviewState.TRAVELING:
            color = (*COLORS["ORANGE"][:3], 128)  # Semi-transparent orange
            border_color = COLORS["ORANGE"]
            status_text = (
                "Hero Traveling" if self.hero_traveling_to_build else "Move Hero Here"
            )
        else:  # INVALID
            color = (*COLORS["RED"][:3], 128)  # Semi-transparent red
            border_color = COLORS["RED"]
            status_text = "Invalid Placement"

        # Draw preview (need to create a surface for alpha blending)
        preview_surface = pygame.Surface(
            (size[0] * TILE_SIZE, size[1] * TILE_SIZE), pygame.SRCALPHA
        )
        preview_surface.fill(color)
        screen.blit(preview_surface, (screen_x, screen_y))

        # Draw border
        pygame.draw.rect(screen, border_color, preview_rect, 2)

        # Draw building name
        font = pygame.font.Font(None, 24)
        name_text = font.render(
            building_type.value.replace("_", " "), True, COLORS["WHITE"]
        )
        text_rect = name_text.get_rect()
        text_rect.center = (int(screen_x + preview_rect.width // 2), int(screen_y - 20))
        screen.blit(name_text, text_rect)

        # Draw status text
        if state != BuildingPreviewState.VALID:
            small_font = pygame.font.Font(None, 18)
            status_surface = small_font.render(status_text, True, border_color)
            status_rect = status_surface.get_rect()
            status_rect.center = (
                int(screen_x + preview_rect.width // 2),
                int(screen_y + preview_rect.height + 10),
            )
            screen.blit(status_surface, status_rect)

    def is_placing(self) -> bool:
        """Check if currently placing a building"""
        return self.building_type is not None

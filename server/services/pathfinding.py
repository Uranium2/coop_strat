import heapq
from typing import List, Optional, Set, Tuple

from shared.models.game_models import Position, TileType


class PathfindingNode:
    def __init__(
        self, x: int, y: int, g_cost: float = 0, h_cost: float = 0, parent=None
    ):
        self.x = x
        self.y = y
        self.g_cost = g_cost  # Distance from start
        self.h_cost = h_cost  # Heuristic distance to goal
        self.f_cost = g_cost + h_cost  # Total cost
        self.parent = parent

    def __lt__(self, other):
        return self.f_cost < other.f_cost

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y

    def __hash__(self):
        return hash((self.x, self.y))


class Pathfinder:
    def __init__(self, map_width: int, map_height: int):
        self.map_width = map_width
        self.map_height = map_height
        # NavMesh will be added later
        self.navmesh_pathfinder = None
        self.navmesh_initialized = False

    def heuristic(self, x1: int, y1: int, x2: int, y2: int) -> float:
        """Manhattan distance heuristic"""
        return abs(x1 - x2) + abs(y1 - y2)

    def get_neighbors(self, x: int, y: int) -> List[Tuple[int, int]]:
        """Get valid neighboring positions (8-directional movement)"""
        neighbors = []
        directions = [
            (-1, -1),
            (-1, 0),
            (-1, 1),
            (0, -1),
            (0, 1),
            (1, -1),
            (1, 0),
            (1, 1),
        ]

        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            if 0 <= nx < self.map_width and 0 <= ny < self.map_height:
                neighbors.append((nx, ny))

        return neighbors

    def is_walkable(
        self, x: int, y: int, game_state, excluding_hero_id: Optional[str] = None
    ) -> bool:
        """Check if a tile is walkable (no static obstacles, accounting for collision radius)"""
        # Check map bounds
        if x < 0 or x >= self.map_width or y < 0 or y >= self.map_height:
            return False

        # Hero collision radius - same as used in game_manager.py
        collision_radius = 0.4

        # Check if the hero (with collision radius) would fit at this tile center
        hero_center_x = x + 0.5  # Tile center
        hero_center_y = y + 0.5

        # Check all tiles that the hero's collision box would overlap
        min_check_x = int(hero_center_x - collision_radius)
        max_check_x = int(hero_center_x + collision_radius) + 1
        min_check_y = int(hero_center_y - collision_radius)
        max_check_y = int(hero_center_y + collision_radius) + 1

        for check_y in range(min_check_y, max_check_y):
            for check_x in range(min_check_x, max_check_x):
                # Check if this tile is within collision radius
                tile_center_x = check_x + 0.5
                tile_center_y = check_y + 0.5

                # Calculate overlap between hero's collision box and this tile
                hero_left = hero_center_x - collision_radius
                hero_right = hero_center_x + collision_radius
                hero_top = hero_center_y - collision_radius
                hero_bottom = hero_center_y + collision_radius

                tile_left = check_x
                tile_right = check_x + 1
                tile_top = check_y
                tile_bottom = check_y + 1

                # Check if hero's collision box overlaps this tile
                if (
                    hero_right > tile_left
                    and hero_left < tile_right
                    and hero_bottom > tile_top
                    and hero_top < tile_bottom
                ):
                    # Check if this overlapping tile is blocked
                    if (
                        check_x < 0
                        or check_x >= self.map_width
                        or check_y < 0
                        or check_y >= self.map_height
                    ):
                        return False

                    tile_type = game_state.map_data[check_y][check_x]
                    if tile_type in [TileType.WOOD, TileType.WALL]:
                        return False

        # Check buildings (static obstacles) with collision radius
        for building in game_state.buildings.values():
            if building.health <= 0:
                continue

            building_x = building.position.x
            building_y = building.position.y
            width, height = building.size

            # Expand building bounds by collision radius
            if (
                building_x - collision_radius
                <= hero_center_x
                <= building_x + width + collision_radius
                and building_y - collision_radius
                <= hero_center_y
                <= building_y + height + collision_radius
            ):
                return False

        return True

    def find_path(
        self,
        start_x: float,
        start_y: float,
        goal_x: float,
        goal_y: float,
        game_state,
        excluding_hero_id: Optional[str] = None,
    ) -> List[Position]:
        """Find path using A* algorithm"""
        start_tile_x, start_tile_y = int(start_x), int(start_y)
        goal_tile_x, goal_tile_y = int(goal_x), int(goal_y)

        # If goal is not walkable, find nearest walkable tile
        if not self.is_walkable(
            goal_tile_x, goal_tile_y, game_state, excluding_hero_id
        ):
            nearest_result = self.find_nearest_walkable(
                goal_tile_x, goal_tile_y, game_state, excluding_hero_id
            )
            if nearest_result[0] is None or nearest_result[1] is None:
                return []  # No path possible
            goal_tile_x, goal_tile_y = nearest_result

        open_set = []
        closed_set: Set[Tuple[int, int]] = set()

        start_node = PathfindingNode(
            start_tile_x,
            start_tile_y,
            0,
            self.heuristic(start_tile_x, start_tile_y, goal_tile_x, goal_tile_y),
        )
        heapq.heappush(open_set, start_node)

        nodes_dict = {(start_tile_x, start_tile_y): start_node}

        while open_set:
            current = heapq.heappop(open_set)

            if (current.x, current.y) in closed_set:
                continue

            closed_set.add((current.x, current.y))

            # Goal reached
            if current.x == goal_tile_x and current.y == goal_tile_y:
                return self.reconstruct_path(current, start_x, start_y, goal_x, goal_y)

            # Check neighbors
            for nx, ny in self.get_neighbors(current.x, current.y):
                if (nx, ny) in closed_set:
                    continue

                if not self.is_walkable(nx, ny, game_state, excluding_hero_id):
                    continue

                # Calculate costs
                diagonal = abs(nx - current.x) + abs(ny - current.y) == 2
                move_cost = 1.414 if diagonal else 1.0  # Diagonal movement costs more

                tentative_g = current.g_cost + move_cost

                if (nx, ny) not in nodes_dict:
                    neighbor = PathfindingNode(
                        nx,
                        ny,
                        tentative_g,
                        self.heuristic(nx, ny, goal_tile_x, goal_tile_y),
                        current,
                    )
                    nodes_dict[(nx, ny)] = neighbor
                    heapq.heappush(open_set, neighbor)
                else:
                    neighbor = nodes_dict[(nx, ny)]
                    if tentative_g < neighbor.g_cost:
                        neighbor.g_cost = tentative_g
                        neighbor.f_cost = neighbor.g_cost + neighbor.h_cost
                        neighbor.parent = current
                        heapq.heappush(open_set, neighbor)

        return []  # No path found

    def find_nearest_walkable(
        self, x: int, y: int, game_state, excluding_hero_id: Optional[str] = None
    ) -> Tuple[Optional[int], Optional[int]]:
        """Find the nearest walkable tile to the given position"""
        if self.is_walkable(x, y, game_state, excluding_hero_id):
            return x, y

        # Search in expanding squares
        for radius in range(1, min(self.map_width, self.map_height)):
            for dx in range(-radius, radius + 1):
                for dy in range(-radius, radius + 1):
                    if abs(dx) == radius or abs(dy) == radius:  # Only check perimeter
                        nx, ny = x + dx, y + dy
                        if (
                            0 <= nx < self.map_width
                            and 0 <= ny < self.map_height
                            and self.is_walkable(nx, ny, game_state, excluding_hero_id)
                        ):
                            return nx, ny

        return None, None

    def reconstruct_path(
        self,
        goal_node: PathfindingNode,
        start_x: float,
        start_y: float,
        goal_x: float,
        goal_y: float,
    ) -> List[Position]:
        """Reconstruct path from goal to start with smoothing"""
        # First, build the raw tile-based path with slight randomization for more natural movement
        raw_path = []
        current = goal_node

        while current:
            # Add slight offset from tile center for more natural paths
            offset_x = 0.0
            offset_y = 0.0

            # Only offset intermediate waypoints, not start/end
            if current.parent and current != goal_node:
                # Small random offset (±0.2 from center) to avoid perfectly grid-aligned movement
                offset_x = (
                    (current.x * 17 + current.y * 23) % 41 - 20
                ) * 0.01  # Deterministic "random"
                offset_y = ((current.x * 31 + current.y * 13) % 37 - 18) * 0.01

            x = float(current.x + 0.5 + offset_x)
            y = float(current.y + 0.5 + offset_y)
            raw_path.append(Position(x=x, y=y))
            current = current.parent

        raw_path.reverse()

        # Replace first position with exact start
        if raw_path:
            raw_path[0] = Position(x=start_x, y=start_y)

        # Replace last position with exact goal
        if raw_path and len(raw_path) > 1:
            raw_path[-1] = Position(x=goal_x, y=goal_y)

        # Apply simple path smoothing by removing redundant waypoints
        if len(raw_path) <= 2:
            return raw_path

        return self._smooth_path_simple(raw_path)

    def _smooth_path_simple(self, path: List[Position]) -> List[Position]:
        """Simple path smoothing by removing waypoints that are nearly collinear"""
        if len(path) <= 2:
            return path

        smoothed = [path[0]]  # Always keep start point

        i = 0
        while i < len(path) - 1:
            # Look ahead to see if we can skip intermediate waypoints
            j = i + 1

            # Try to extend the line as far as possible
            while j < len(path) - 1:
                # Check if the three points are roughly collinear
                if self._are_points_roughly_collinear(path[i], path[j], path[j + 1]):
                    j += 1
                else:
                    break

            # Add the furthest point we can reach in a straight line
            smoothed.append(path[j])
            i = j

        return smoothed

    def _are_points_roughly_collinear(
        self, p1: Position, p2: Position, p3: Position
    ) -> bool:
        """Check if three points are roughly in a straight line"""
        # Calculate vectors
        v1_x = p2.x - p1.x
        v1_y = p2.y - p1.y
        v2_x = p3.x - p2.x
        v2_y = p3.y - p2.y

        # If either vector is very short, consider them collinear
        if (abs(v1_x) < 0.1 and abs(v1_y) < 0.1) or (
            abs(v2_x) < 0.1 and abs(v2_y) < 0.1
        ):
            return True

        # Calculate cross product (measures how "perpendicular" the vectors are)
        cross_product = abs(v1_x * v2_y - v1_y * v2_x)

        # Calculate the magnitudes
        mag1 = (v1_x * v1_x + v1_y * v1_y) ** 0.5
        mag2 = (v2_x * v2_x + v2_y * v2_y) ** 0.5

        if mag1 < 0.01 or mag2 < 0.01:
            return True

        # Normalize the cross product by the magnitudes
        normalized_cross = cross_product / (mag1 * mag2)

        # If the normalized cross product is small, the vectors are nearly parallel
        return normalized_cross < 0.3  # Adjust this threshold for more/less smoothing


# Legacy compatibility class
class PathfindingService:
    def __init__(self, map_width: int, map_height: int):
        self.pathfinder = Pathfinder(map_width, map_height)

    def find_path(
        self, start: Position, goal: Position, obstacles: List[Position]
    ) -> List[Position]:
        # This is kept for compatibility but not used in the new system
        return []

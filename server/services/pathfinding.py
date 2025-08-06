import heapq
import math
from typing import List, Tuple, Optional, Set
from shared.models.game_models import Position, TileType

class PathfindingNode:
    def __init__(self, x: int, y: int, g_cost: float = 0, h_cost: float = 0, parent=None):
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
        
    def heuristic(self, x1: int, y1: int, x2: int, y2: int) -> float:
        """Manhattan distance heuristic"""
        return abs(x1 - x2) + abs(y1 - y2)
    
    def get_neighbors(self, x: int, y: int) -> List[Tuple[int, int]]:
        """Get valid neighboring positions (8-directional movement)"""
        neighbors = []
        directions = [
            (-1, -1), (-1, 0), (-1, 1),
            (0, -1),           (0, 1),
            (1, -1),  (1, 0),  (1, 1)
        ]
        
        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            if 0 <= nx < self.map_width and 0 <= ny < self.map_height:
                neighbors.append((nx, ny))
        
        return neighbors
    
    def is_walkable(self, x: int, y: int, game_state, excluding_hero_id: str = None) -> bool:
        """Check if a tile is walkable (no static obstacles)"""
        # Check map bounds
        if x < 0 or x >= self.map_width or y < 0 or y >= self.map_height:
            return False
        
        # Check tile type
        tile_type = game_state.map_data[y][x]
        if tile_type in [TileType.WOOD, TileType.WALL]:
            return False
        
        # Check buildings (static obstacles)
        for building in game_state.buildings.values():
            if building.health <= 0:
                continue
            
            building_x = int(building.position.x)
            building_y = int(building.position.y)
            width, height = building.size
            
            if (building_x <= x < building_x + width and 
                building_y <= y < building_y + height):
                return False
        
        return True
    
    def find_path(self, start_x: float, start_y: float, goal_x: float, goal_y: float, 
                  game_state, excluding_hero_id: str = None) -> List[Position]:
        """Find path using A* algorithm"""
        start_tile_x, start_tile_y = int(start_x), int(start_y)
        goal_tile_x, goal_tile_y = int(goal_x), int(goal_y)
        
        # If goal is not walkable, find nearest walkable tile
        if not self.is_walkable(goal_tile_x, goal_tile_y, game_state, excluding_hero_id):
            goal_tile_x, goal_tile_y = self.find_nearest_walkable(goal_tile_x, goal_tile_y, game_state, excluding_hero_id)
            if goal_tile_x is None:
                return []  # No path possible
        
        open_set = []
        closed_set: Set[Tuple[int, int]] = set()
        
        start_node = PathfindingNode(start_tile_x, start_tile_y, 0, 
                                   self.heuristic(start_tile_x, start_tile_y, goal_tile_x, goal_tile_y))
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
                    neighbor = PathfindingNode(nx, ny, tentative_g, 
                                             self.heuristic(nx, ny, goal_tile_x, goal_tile_y), current)
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
    
    def find_nearest_walkable(self, x: int, y: int, game_state, excluding_hero_id: str = None) -> Tuple[Optional[int], Optional[int]]:
        """Find the nearest walkable tile to the given position"""
        if self.is_walkable(x, y, game_state, excluding_hero_id):
            return x, y
        
        # Search in expanding squares
        for radius in range(1, min(self.map_width, self.map_height)):
            for dx in range(-radius, radius + 1):
                for dy in range(-radius, radius + 1):
                    if abs(dx) == radius or abs(dy) == radius:  # Only check perimeter
                        nx, ny = x + dx, y + dy
                        if (0 <= nx < self.map_width and 0 <= ny < self.map_height and
                            self.is_walkable(nx, ny, game_state, excluding_hero_id)):
                            return nx, ny
        
        return None, None
    
    def reconstruct_path(self, goal_node: PathfindingNode, start_x: float, start_y: float, 
                        goal_x: float, goal_y: float) -> List[Position]:
        """Reconstruct path from goal to start"""
        path = []
        current = goal_node
        
        while current:
            path.append(Position(x=float(current.x + 0.5), y=float(current.y + 0.5)))
            current = current.parent
        
        path.reverse()
        
        # Replace first position with exact start
        if path:
            path[0] = Position(x=start_x, y=start_y)
        
        # Replace last position with exact goal (if it's walkable)
        if path and len(path) > 1:
            path[-1] = Position(x=goal_x, y=goal_y)
        
        return path

# Legacy compatibility class
class PathfindingService:
    def __init__(self, map_width: int, map_height: int):
        self.pathfinder = Pathfinder(map_width, map_height)
        
    def find_path(self, start: Position, goal: Position, obstacles: List[Position]) -> List[Position]:
        # This is kept for compatibility but not used in the new system
        return []
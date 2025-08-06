from collections import deque
from typing import List, Tuple, Optional
from shared.models.game_models import Position

class PathfindingService:
    def __init__(self, map_width: int, map_height: int):
        self.map_width = map_width
        self.map_height = map_height
    
    def find_path(self, start: Position, goal: Position, obstacles: List[Position]) -> List[Position]:
        if start.x == goal.x and start.y == goal.y:
            return []
        
        obstacle_set = set((obs.x, obs.y) for obs in obstacles)
        
        queue = deque([(start.x, start.y, [])])
        visited = set()
        visited.add((start.x, start.y))
        
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0), (1, 1), (-1, -1), (1, -1), (-1, 1)]
        
        while queue:
            x, y, path = queue.popleft()
            
            if len(path) > 50:
                continue
            
            for dx, dy in directions:
                nx, ny = x + dx, y + dy
                
                if (0 <= nx < self.map_width and 0 <= ny < self.map_height and
                    (nx, ny) not in visited and (nx, ny) not in obstacle_set):
                    
                    new_path = path + [Position(x=nx, y=ny)]
                    
                    if nx == goal.x and ny == goal.y:
                        return new_path
                    
                    if len(new_path) < 50:
                        queue.append((nx, ny, new_path))
                        visited.add((nx, ny))
        
        return self._get_direct_path(start, goal)
    
    def _get_direct_path(self, start: Position, goal: Position) -> List[Position]:
        path = []
        current_x, current_y = start.x, start.y
        
        while current_x != goal.x or current_y != goal.y:
            if current_x < goal.x:
                current_x += 1
            elif current_x > goal.x:
                current_x -= 1
            
            if current_y < goal.y:
                current_y += 1
            elif current_y > goal.y:
                current_y -= 1
            
            path.append(Position(x=current_x, y=current_y))
            
            if len(path) > 100:
                break
        
        return path
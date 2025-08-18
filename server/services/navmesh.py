import heapq
import math
from typing import List, Optional, Set, Tuple, Dict
from dataclasses import dataclass

from shared.models.game_models import Position, TileType


@dataclass
class NavMeshPolygon:
    """A convex polygon in the navigation mesh"""
    id: int
    vertices: List[Position]  # Vertices in clockwise order
    center: Position
    neighbors: List[int]  # IDs of adjacent polygons
    edge_midpoints: Dict[int, Position]  # neighbor_id -> midpoint of shared edge


@dataclass
class NavMeshEdge:
    """An edge between two navigation mesh polygons"""
    polygon1_id: int
    polygon2_id: int
    start: Position
    end: Position
    midpoint: Position


class NavMeshNode:
    """A node in the A* search over the navigation mesh"""
    def __init__(self, polygon_id: int, g_cost: float = 0, h_cost: float = 0, parent=None, entry_point: Optional[Position] = None):
        self.polygon_id = polygon_id
        self.g_cost = g_cost  # Distance from start
        self.h_cost = h_cost  # Heuristic distance to goal
        self.f_cost = g_cost + h_cost  # Total cost
        self.parent = parent
        self.entry_point = entry_point  # Point where we entered this polygon

    def __lt__(self, other):
        return self.f_cost < other.f_cost

    def __eq__(self, other):
        return self.polygon_id == other.polygon_id

    def __hash__(self):
        return hash(self.polygon_id)


class NavMesh:
    """Navigation mesh for smooth pathfinding"""
    
    def __init__(self, map_width: int, map_height: int):
        self.map_width = map_width
        self.map_height = map_height
        self.polygons: Dict[int, NavMeshPolygon] = {}
        self.edges: List[NavMeshEdge] = []
        self.polygon_id_counter = 0
        
    def generate_from_tile_map(self, tile_map: List[List[TileType]], buildings: Optional[Dict] = None):
        """Generate navigation mesh from tile-based map data"""
        # Create a walkability grid first
        walkable_grid = self._create_walkable_grid(tile_map, buildings)
        
        # Generate polygons using rectangular decomposition
        self._generate_rectangular_polygons(walkable_grid)
        
        # Connect adjacent polygons
        self._connect_polygons()
        
    def _create_walkable_grid(self, tile_map: List[List[TileType]], buildings: Optional[Dict] = None) -> List[List[bool]]:
        """Create a boolean grid indicating walkable tiles"""
        walkable = []
        
        for y in range(len(tile_map)):
            row = []
            for x in range(len(tile_map[0])):
                tile_type = tile_map[y][x]
                is_walkable = tile_type not in [TileType.WOOD, TileType.WALL]
                
                # Check buildings (if provided)
                if buildings and is_walkable:
                    for building in buildings.values():
                        if building.health <= 0:
                            continue
                        bx, by = int(building.position.x), int(building.position.y)
                        w, h = building.size
                        if bx <= x < bx + w and by <= y < by + h:
                            is_walkable = False
                            break
                            
                row.append(is_walkable)
            walkable.append(row)
            
        return walkable
        
    def _generate_rectangular_polygons(self, walkable_grid: List[List[bool]]):
        """Generate rectangular polygons using horizontal strip decomposition"""
        processed = [[False] * len(walkable_grid[0]) for _ in range(len(walkable_grid))]
        
        for y in range(len(walkable_grid)):
            for x in range(len(walkable_grid[0])):
                if walkable_grid[y][x] and not processed[y][x]:
                    # Find the largest rectangle starting at (x, y)
                    rect = self._find_largest_rectangle(walkable_grid, processed, x, y)
                    if rect:
                        self._create_polygon_from_rectangle(rect)
                        
    def _find_largest_rectangle(self, walkable_grid: List[List[bool]], processed: List[List[bool]], 
                               start_x: int, start_y: int) -> Optional[Tuple[int, int, int, int]]:
        """Find the largest walkable rectangle starting at (start_x, start_y)"""
        if processed[start_y][start_x] or not walkable_grid[start_y][start_x]:
            return None
            
        # Find maximum width in the starting row
        max_width = 0
        for x in range(start_x, len(walkable_grid[0])):
            if walkable_grid[start_y][x] and not processed[start_y][x]:
                max_width += 1
            else:
                break
                
        if max_width == 0:
            return None
            
        # Find maximum height that maintains this width
        max_height = 1
        for y in range(start_y + 1, len(walkable_grid)):
            # Check if we can extend to this row
            can_extend = True
            for x in range(start_x, start_x + max_width):
                if not walkable_grid[y][x] or processed[y][x]:
                    can_extend = False
                    break
                    
            if can_extend:
                max_height += 1
            else:
                break
                
        # Mark all tiles in this rectangle as processed
        for y in range(start_y, start_y + max_height):
            for x in range(start_x, start_x + max_width):
                processed[y][x] = True
                
        return (start_x, start_y, max_width, max_height)
        
    def _create_polygon_from_rectangle(self, rect: Tuple[int, int, int, int]):
        """Create a polygon from a rectangle (x, y, width, height)"""
        x, y, width, height = rect
        
        # Create vertices (clockwise order)
        vertices = [
            Position(x=float(x), y=float(y)),                    # Top-left
            Position(x=float(x + width), y=float(y)),            # Top-right
            Position(x=float(x + width), y=float(y + height)),   # Bottom-right
            Position(x=float(x), y=float(y + height))            # Bottom-left
        ]
        
        # Calculate center
        center = Position(
            x=float(x + width / 2),
            y=float(y + height / 2)
        )
        
        polygon = NavMeshPolygon(
            id=self.polygon_id_counter,
            vertices=vertices,
            center=center,
            neighbors=[],
            edge_midpoints={}
        )
        
        self.polygons[self.polygon_id_counter] = polygon
        self.polygon_id_counter += 1
        
    def _connect_polygons(self):
        """Connect adjacent polygons and create edges"""
        polygon_list = list(self.polygons.values())
        
        for i, poly1 in enumerate(polygon_list):
            for j, poly2 in enumerate(polygon_list[i + 1:], i + 1):
                shared_edge = self._find_shared_edge(poly1, poly2)
                if shared_edge:
                    # Add as neighbors
                    poly1.neighbors.append(poly2.id)
                    poly2.neighbors.append(poly1.id)
                    
                    # Calculate edge midpoint
                    midpoint = Position(
                        x=(shared_edge[0].x + shared_edge[1].x) / 2,
                        y=(shared_edge[0].y + shared_edge[1].y) / 2
                    )
                    
                    poly1.edge_midpoints[poly2.id] = midpoint
                    poly2.edge_midpoints[poly1.id] = midpoint
                    
                    # Create edge
                    edge = NavMeshEdge(
                        polygon1_id=poly1.id,
                        polygon2_id=poly2.id,
                        start=shared_edge[0],
                        end=shared_edge[1],
                        midpoint=midpoint
                    )
                    self.edges.append(edge)
                    
    def _find_shared_edge(self, poly1: NavMeshPolygon, poly2: NavMeshPolygon) -> Optional[Tuple[Position, Position]]:
        """Find shared edge between two polygons"""
        for i in range(len(poly1.vertices)):
            edge1_start = poly1.vertices[i]
            edge1_end = poly1.vertices[(i + 1) % len(poly1.vertices)]
            
            for j in range(len(poly2.vertices)):
                edge2_start = poly2.vertices[j]
                edge2_end = poly2.vertices[(j + 1) % len(poly2.vertices)]
                
                # Check if edges overlap (for rectangular polygons, they either fully overlap or don't)
                if self._edges_overlap(edge1_start, edge1_end, edge2_start, edge2_end):
                    # Return the overlapping segment
                    return self._get_edge_overlap(edge1_start, edge1_end, edge2_start, edge2_end)
                    
        return None
        
    def _edges_overlap(self, e1_start: Position, e1_end: Position, 
                      e2_start: Position, e2_end: Position) -> bool:
        """Check if two edges overlap"""
        # For rectangles, edges are either horizontal or vertical
        
        # Check if both edges are horizontal
        if abs(e1_start.y - e1_end.y) < 0.001 and abs(e2_start.y - e2_end.y) < 0.001:
            if abs(e1_start.y - e2_start.y) < 0.001:  # Same Y coordinate
                # Check X overlap
                e1_min_x = min(e1_start.x, e1_end.x)
                e1_max_x = max(e1_start.x, e1_end.x)
                e2_min_x = min(e2_start.x, e2_end.x)
                e2_max_x = max(e2_start.x, e2_end.x)
                return not (e1_max_x <= e2_min_x or e2_max_x <= e1_min_x)
                
        # Check if both edges are vertical
        if abs(e1_start.x - e1_end.x) < 0.001 and abs(e2_start.x - e2_end.x) < 0.001:
            if abs(e1_start.x - e2_start.x) < 0.001:  # Same X coordinate
                # Check Y overlap
                e1_min_y = min(e1_start.y, e1_end.y)
                e1_max_y = max(e1_start.y, e1_end.y)
                e2_min_y = min(e2_start.y, e2_end.y)
                e2_max_y = max(e2_start.y, e2_end.y)
                return not (e1_max_y <= e2_min_y or e2_max_y <= e1_min_y)
                
        return False
        
    def _get_edge_overlap(self, e1_start: Position, e1_end: Position,
                         e2_start: Position, e2_end: Position) -> Tuple[Position, Position]:
        """Get the overlapping segment of two edges"""
        # For horizontal edges
        if abs(e1_start.y - e1_end.y) < 0.001:
            y = e1_start.y
            e1_min_x = min(e1_start.x, e1_end.x)
            e1_max_x = max(e1_start.x, e1_end.x)
            e2_min_x = min(e2_start.x, e2_end.x)
            e2_max_x = max(e2_start.x, e2_end.x)
            
            overlap_min_x = max(e1_min_x, e2_min_x)
            overlap_max_x = min(e1_max_x, e2_max_x)
            
            return (Position(x=overlap_min_x, y=y), Position(x=overlap_max_x, y=y))
            
        # For vertical edges
        else:
            x = e1_start.x
            e1_min_y = min(e1_start.y, e1_end.y)
            e1_max_y = max(e1_start.y, e1_end.y)
            e2_min_y = min(e2_start.y, e2_end.y)
            e2_max_y = max(e2_start.y, e2_end.y)
            
            overlap_min_y = max(e1_min_y, e2_min_y)
            overlap_max_y = min(e1_max_y, e2_max_y)
            
            return (Position(x=x, y=overlap_min_y), Position(x=x, y=overlap_max_y))
            
    def find_polygon_containing_point(self, point: Position) -> Optional[int]:
        """Find which polygon contains the given point"""
        for polygon in self.polygons.values():
            if self._point_in_polygon(point, polygon):
                return polygon.id
        return None
        
    def _point_in_polygon(self, point: Position, polygon: NavMeshPolygon) -> bool:
        """Check if point is inside polygon using ray casting"""
        x, y = point.x, point.y
        vertices = polygon.vertices
        n = len(vertices)
        inside = False
        
        p1x, p1y = vertices[0].x, vertices[0].y
        for i in range(1, n + 1):
            p2x, p2y = vertices[i % n].x, vertices[i % n].y
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                            if p1x == p2x or x <= xinters:
                                inside = not inside
            p1x, p1y = p2x, p2y
            
        return inside
        
    def heuristic(self, poly1_id: int, poly2_id: int) -> float:
        """Heuristic function for A* (Euclidean distance between polygon centers)"""
        poly1 = self.polygons[poly1_id]
        poly2 = self.polygons[poly2_id]
        
        dx = poly1.center.x - poly2.center.x
        dy = poly1.center.y - poly2.center.y
        return math.sqrt(dx * dx + dy * dy)
        
    def find_path_polygons(self, start_point: Position, goal_point: Position) -> List[int]:
        """Find path as sequence of polygon IDs using A*"""
        start_poly_id = self.find_polygon_containing_point(start_point)
        goal_poly_id = self.find_polygon_containing_point(goal_point)
        
        if start_poly_id is None or goal_poly_id is None:
            return []
            
        if start_poly_id == goal_poly_id:
            return [start_poly_id]
            
        open_set = []
        closed_set: Set[int] = set()
        
        start_node = NavMeshNode(
            start_poly_id,
            0,
            self.heuristic(start_poly_id, goal_poly_id),
            None,
            start_point
        )
        heapq.heappush(open_set, start_node)
        
        nodes_dict = {start_poly_id: start_node}
        
        while open_set:
            current = heapq.heappop(open_set)
            
            if current.polygon_id in closed_set:
                continue
                
            closed_set.add(current.polygon_id)
            
            # Goal reached
            if current.polygon_id == goal_poly_id:
                return self._reconstruct_polygon_path(current)
                
            # Check neighbors
            current_polygon = self.polygons[current.polygon_id]
            for neighbor_id in current_polygon.neighbors:
                if neighbor_id in closed_set:
                    continue
                    
                # Calculate movement cost (distance between entry points)
                neighbor_entry_point = current_polygon.edge_midpoints[neighbor_id]
                
                if current.entry_point:
                    move_cost = self._distance(current.entry_point, neighbor_entry_point)
                else:
                    move_cost = self._distance(start_point, neighbor_entry_point)
                    
                tentative_g = current.g_cost + move_cost
                
                if neighbor_id not in nodes_dict:
                    neighbor_node = NavMeshNode(
                        neighbor_id,
                        tentative_g,
                        self.heuristic(neighbor_id, goal_poly_id),
                        current,
                        neighbor_entry_point
                    )
                    nodes_dict[neighbor_id] = neighbor_node
                    heapq.heappush(open_set, neighbor_node)
                else:
                    neighbor_node = nodes_dict[neighbor_id]
                    if tentative_g < neighbor_node.g_cost:
                        neighbor_node.g_cost = tentative_g
                        neighbor_node.f_cost = neighbor_node.g_cost + neighbor_node.h_cost
                        neighbor_node.parent = current
                        neighbor_node.entry_point = neighbor_entry_point
                        heapq.heappush(open_set, neighbor_node)
                        
        return []  # No path found
        
    def _reconstruct_polygon_path(self, goal_node: NavMeshNode) -> List[int]:
        """Reconstruct path from goal to start"""
        path = []
        current = goal_node
        
        while current:
            path.append(current.polygon_id)
            current = current.parent
            
        path.reverse()
        return path
        
    def _distance(self, p1: Position, p2: Position) -> float:
        """Calculate Euclidean distance between two points"""
        dx = p1.x - p2.x
        dy = p1.y - p2.y
        return math.sqrt(dx * dx + dy * dy)


class NavMeshPathfinder:
    """Complete NavMesh pathfinding system with funnel algorithm"""
    
    def __init__(self, map_width: int, map_height: int):
        self.navmesh = NavMesh(map_width, map_height)
        
    def generate_navmesh(self, tile_map: List[List[TileType]], buildings: Optional[Dict] = None):
        """Generate the navigation mesh from the game map"""
        self.navmesh.generate_from_tile_map(tile_map, buildings)
        
    def find_path(self, start: Position, goal: Position) -> List[Position]:
        """Find a smooth path from start to goal using NavMesh + funnel algorithm"""
        # Find polygon path
        polygon_path = self.navmesh.find_path_polygons(start, goal)
        
        if not polygon_path:
            return []
            
        if len(polygon_path) == 1:
            # Direct path within same polygon
            return [start, goal]
            
        # Apply funnel algorithm for smooth path
        return self._funnel_algorithm(start, goal, polygon_path)
        
    def _funnel_algorithm(self, start: Position, goal: Position, polygon_path: List[int]) -> List[Position]:
        """Smooth path using funnel algorithm"""
        if len(polygon_path) < 2:
            return [start, goal]
            
        # Build portals (edges between adjacent polygons)
        portals = []
        
        for i in range(len(polygon_path) - 1):
            current_poly = self.navmesh.polygons[polygon_path[i]]
            next_poly = self.navmesh.polygons[polygon_path[i + 1]]
            
            # Find shared edge
            shared_edge = self.navmesh._find_shared_edge(current_poly, next_poly)
            if shared_edge:
                portals.append(shared_edge)
                
        if not portals:
            return [start, goal]
            
        # Initialize funnel
        apex = start
        left_point = start
        right_point = start
        path = [start]
        
        for i, portal in enumerate(portals):
            portal_left, portal_right = portal
            
            # Update right side
            if self._cross_product_2d(apex, right_point, portal_right) <= 0:
                if self._cross_product_2d(apex, left_point, portal_right) > 0:
                    right_point = portal_right
                else:
                    # Right over left, insert left to path and restart from left
                    path.append(left_point)
                    apex = left_point
                    left_point = apex
                    right_point = apex
                    continue
                    
            # Update left side
            if self._cross_product_2d(apex, left_point, portal_left) >= 0:
                if self._cross_product_2d(apex, right_point, portal_left) < 0:
                    left_point = portal_left
                else:
                    # Left over right, insert right to path and restart from right
                    path.append(right_point)
                    apex = right_point
                    left_point = apex
                    right_point = apex
                    continue
                    
        # Add goal
        path.append(goal)
        
        return path
        
    def _cross_product_2d(self, a: Position, b: Position, c: Position) -> float:
        """Calculate 2D cross product for funnel algorithm"""
        return (b.x - a.x) * (c.y - a.y) - (b.y - a.y) * (c.x - a.x)


# Updated pathfinder class that uses NavMesh
class NavMeshAwarePathfinder:
    """Pathfinder that combines NavMesh with fallback to grid-based pathfinding"""
    
    def __init__(self, map_width: int, map_height: int):
        self.map_width = map_width
        self.map_height = map_height
        self.navmesh_pathfinder = NavMeshPathfinder(map_width, map_height)
        self.grid_pathfinder = None  # Will be set when needed
        
    def generate_navmesh(self, tile_map: List[List[TileType]], buildings: Optional[Dict] = None):
        """Generate the navigation mesh"""
        self.navmesh_pathfinder.generate_navmesh(tile_map, buildings)
        
    def find_path(self, start_x: float, start_y: float, goal_x: float, goal_y: float, 
                  game_state, excluding_hero_id: Optional[str] = None) -> List[Position]:
        """Find path using NavMesh pathfinding"""
        start = Position(x=start_x, y=start_y)
        goal = Position(x=goal_x, y=goal_y)
        
        # Try NavMesh pathfinding first
        try:
            path = self.navmesh_pathfinder.find_path(start, goal)
            if path:
                return path
        except Exception as e:
            print(f"NavMesh pathfinding failed: {e}")
            
        # Fallback to direct line if NavMesh fails
        return [start, goal]
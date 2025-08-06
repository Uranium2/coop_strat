import random
from typing import List, Tuple

import numpy as np

from shared.constants.game_constants import MAP_HEIGHT, MAP_WIDTH
from shared.models.game_models import TileType


class MapGenerator:
    def __init__(
        self, width: int = MAP_WIDTH, height: int = MAP_HEIGHT, seed: int = None
    ):
        self.width = width
        self.height = height
        if seed:
            random.seed(seed)
            np.random.seed(seed)

    def generate_map(self) -> List[List[TileType]]:
        map_data = [
            [TileType.EMPTY for _ in range(self.width)] for _ in range(self.height)
        ]

        center_x, center_y = self.width // 2, self.height // 2
        clear_radius = 15

        self._place_basic_resources(map_data, center_x, center_y, clear_radius)
        self._place_rare_resources(map_data, center_x, center_y)
        self._ensure_symmetry(map_data, center_x, center_y)

        return map_data

    def _place_basic_resources(
        self,
        map_data: List[List[TileType]],
        center_x: int,
        center_y: int,
        clear_radius: int,
    ):
        basic_resources = [TileType.WOOD, TileType.STONE, TileType.WHEAT]

        for resource in basic_resources:
            clusters = random.randint(8, 12)
            for _ in range(clusters):
                cluster_x = random.randint(clear_radius, self.width - clear_radius)
                cluster_y = random.randint(clear_radius, self.height - clear_radius)

                if (
                    self._distance(cluster_x, cluster_y, center_x, center_y)
                    < clear_radius + 10
                ):
                    continue

                cluster_size = random.randint(3, 8)
                for _ in range(cluster_size):
                    x = cluster_x + random.randint(-3, 3)
                    y = cluster_y + random.randint(-3, 3)

                    if (
                        0 <= x < self.width
                        and 0 <= y < self.height
                        and map_data[y][x] == TileType.EMPTY
                        and self._distance(x, y, center_x, center_y) >= clear_radius
                    ):
                        map_data[y][x] = resource

    def _place_rare_resources(
        self, map_data: List[List[TileType]], center_x: int, center_y: int
    ):
        rare_resources = [TileType.METAL, TileType.GOLD]

        for resource in rare_resources:
            clusters = random.randint(4, 6)
            for _ in range(clusters):
                edge_side = random.randint(0, 3)

                if edge_side == 0:
                    cluster_x = random.randint(5, 25)
                    cluster_y = random.randint(5, self.height - 5)
                elif edge_side == 1:
                    cluster_x = random.randint(self.width - 25, self.width - 5)
                    cluster_y = random.randint(5, self.height - 5)
                elif edge_side == 2:
                    cluster_x = random.randint(5, self.width - 5)
                    cluster_y = random.randint(5, 25)
                else:
                    cluster_x = random.randint(5, self.width - 5)
                    cluster_y = random.randint(self.height - 25, self.height - 5)

                cluster_size = random.randint(2, 4)
                for _ in range(cluster_size):
                    x = cluster_x + random.randint(-2, 2)
                    y = cluster_y + random.randint(-2, 2)

                    if (
                        0 <= x < self.width
                        and 0 <= y < self.height
                        and map_data[y][x] == TileType.EMPTY
                    ):
                        map_data[y][x] = resource

    def _ensure_symmetry(
        self, map_data: List[List[TileType]], center_x: int, center_y: int
    ):
        for y in range(self.height):
            for x in range(self.width):
                if map_data[y][x] != TileType.EMPTY:
                    mirror_x = 2 * center_x - x
                    mirror_y = 2 * center_y - y

                    if (
                        0 <= mirror_x < self.width
                        and 0 <= mirror_y < self.height
                        and map_data[mirror_y][mirror_x] == TileType.EMPTY
                    ):
                        if random.random() < 0.7:
                            map_data[mirror_y][mirror_x] = map_data[y][x]

    def _distance(self, x1: int, y1: int, x2: int, y2: int) -> float:
        return ((x1 - x2) ** 2 + (y1 - y2) ** 2) ** 0.5

    def get_spawn_area(self) -> Tuple[int, int, int, int]:
        center_x, center_y = self.width // 2, self.height // 2
        spawn_radius = 10
        return (
            center_x - spawn_radius,
            center_y - spawn_radius,
            center_x + spawn_radius,
            center_y + spawn_radius,
        )

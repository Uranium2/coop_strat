import json
import os
from typing import Any, Dict, List, Optional

from shared.models.game_models import TileType


class MapLoader:
    """Service for loading custom maps from files"""

    def __init__(self, maps_directory: str = "maps"):
        self.maps_directory = maps_directory

    def list_available_maps(self) -> List[str]:
        """Get list of available map files"""
        if not os.path.exists(self.maps_directory):
            return []

        map_files = [f for f in os.listdir(self.maps_directory) if f.endswith(".json")]
        return sorted(map_files)

    def load_map(self, filename: str) -> Optional[Dict[str, Any]]:
        """Load a map from file

        Returns:
            Dict containing map_data, metadata, etc. or None if failed
        """
        filepath = os.path.join(self.maps_directory, filename)

        if not os.path.exists(filepath):
            print(f"❌ Map file not found: {filepath}")
            return None

        try:
            with open(filepath, "r") as f:
                map_data = json.load(f)

            # Validate required fields
            if "map_data" not in map_data:
                print(f"❌ Invalid map file: missing map_data in {filename}")
                return None

            # Convert string tile types back to TileType enums
            converted_map_data = []
            for row_data in map_data["map_data"]:
                row = []
                for tile_str in row_data:
                    try:
                        tile_type = TileType(tile_str)
                        row.append(tile_type)
                    except ValueError:
                        print(
                            f"⚠️ Unknown tile type '{tile_str}' in {filename}, using EMPTY"
                        )
                        row.append(TileType.EMPTY)
                converted_map_data.append(row)

            # Update map_data with converted types
            map_data["map_data"] = converted_map_data

            # Validate dimensions
            metadata = map_data.get("metadata", {})
            actual_height = len(converted_map_data)
            actual_width = len(converted_map_data[0]) if converted_map_data else 0

            expected_width = metadata.get("width", actual_width)
            expected_height = metadata.get("height", actual_height)

            if actual_width != expected_width or actual_height != expected_height:
                print(f"⚠️ Map dimension mismatch in {filename}")
                print(f"   Expected: {expected_width}x{expected_height}")
                print(f"   Actual: {actual_width}x{actual_height}")

            print(f"✅ Loaded map: {filename} ({actual_width}x{actual_height})")
            return map_data

        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON in map file {filename}: {e}")
            return None
        except Exception as e:
            print(f"❌ Failed to load map {filename}: {e}")
            return None

    def get_map_info(self, filename: str) -> Optional[Dict[str, Any]]:
        """Get map metadata without loading full map data"""
        filepath = os.path.join(self.maps_directory, filename)

        if not os.path.exists(filepath):
            return None

        try:
            with open(filepath, "r") as f:
                map_data = json.load(f)

            metadata = map_data.get("metadata", {})

            # Calculate actual dimensions
            map_tiles = map_data.get("map_data", [])
            actual_height = len(map_tiles)
            actual_width = len(map_tiles[0]) if map_tiles else 0

            return {
                "filename": filename,
                "name": metadata.get("name", filename),
                "created": metadata.get("created", "Unknown"),
                "width": actual_width,
                "height": actual_height,
                "version": metadata.get("version", "1.0"),
            }

        except Exception as e:
            print(f"❌ Failed to read map info for {filename}: {e}")
            return None

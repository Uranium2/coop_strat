# Co-op Strategy RTS - Map Editor

This map editor allows you to create custom maps for the Co-op Strategy RTS game.

## 🚀 Quick Start

### Launch Interactive Editor
```bash
python3 map_editor.py
# or with custom dimensions
python3 map_editor.py --width 50 --height 40
```

### Demo Commands
```bash
# List available maps
python3 map_demo.py --list-maps

# Create a demo map
python3 map_demo.py --create-demo

# Show map information
python3 map_demo.py --info demo_map.json

# Launch interactive editor
python3 map_demo.py --editor
```

## 🎮 Controls

### Interactive Editor
- **WASD/Arrow Keys**: Move camera around the map
- **1-6**: Select tile type (Empty, Wood, Stone, Wheat, Metal, Gold)
- **Left Click**: Place selected tile
- **Right Click**: Clear tile (set to Empty)
- **G**: Toggle grid display
- **Ctrl+S**: Save map to file
- **Ctrl+O**: Load existing map
- **Ctrl+N**: Create new empty map
- **ESC**: Exit editor

### Tile Types
1. **Empty** (Black) - Open space
2. **Wood** (Dark Green) - Wood resource
3. **Stone** (Gray) - Stone resource  
4. **Wheat** (Yellow) - Food resource
5. **Metal** (Silver) - Metal resource
6. **Gold** (Gold) - Rare resource

## 📁 File Format

Maps are saved as JSON files in the `maps/` directory with the following structure:

```json
{
  "metadata": {
    "name": "Custom Map Name",
    "created": "2025-08-13T20:56:25.662139",
    "version": "1.0",
    "width": 30,
    "height": 20,
    "tile_size": 32
  },
  "map_data": [
    ["STONE", "STONE", "EMPTY", ...],
    ["STONE", "WOOD", "WOOD", ...],
    ...
  ],
  "spawn_points": [],
  "objectives": []
}
```

## 🎯 Features

### Current Features
- ✅ **Tile Placement**: Paint different resource and terrain tiles
- ✅ **Camera Movement**: Navigate large maps easily
- ✅ **File Operations**: Save/load custom maps
- ✅ **Grid Display**: Toggle grid for precise placement
- ✅ **Multiple Map Sizes**: Create maps from small to large
- ✅ **Tile Palette**: Easy tile type selection
- ✅ **Map Analysis**: View tile distribution and statistics

### Future Features (Planned)
- 🔄 **Unit Placement**: Place heroes and units on maps
- 🔄 **Building Placement**: Pre-place buildings like Town Halls
- 🔄 **Spawn Points**: Define enemy spawn locations
- 🔄 **Objectives**: Set win/lose conditions
- 🔄 **Save Games**: Full game state save/load
- 🔄 **Multiplayer Setup**: Configure player starting positions

## 📊 Map Statistics

The map editor tracks and displays:
- Total map size (width × height)
- Tile type distribution and percentages
- Resource density analysis
- Map creation metadata

## 🛠️ Technical Details

### Supported Tile Types
- `EMPTY`: Open terrain for building/movement
- `WOOD`: Renewable resource for construction
- `STONE`: Mining resource for buildings
- `WHEAT`: Food resource for units
- `METAL`: Advanced construction material
- `GOLD`: Rare resource for upgrades

### Map Dimensions
- Default: 80×60 tiles
- Customizable via command line arguments
- Tile size: 32×32 pixels
- Maximum recommended: 200×200 tiles

### File Management
- Maps saved to `maps/` directory
- JSON format for easy editing/sharing
- Automatic timestamping
- Metadata preservation

## 🎮 Integration with Game

Custom maps can be loaded into the main game by:
1. Creating maps with the editor
2. Placing map files in the `maps/` directory
3. Using the map loader service in the game server

*Note: Full game integration is planned for future updates.*

## 🐛 Troubleshooting

### Common Issues
- **No maps directory**: The editor will create it automatically
- **File permissions**: Ensure write access to the project directory
- **Large maps**: May require more memory for very large maps (200×200+)
- **Invalid JSON**: Use the editor's save function rather than manual editing

### Getting Help
- Check the console output for error messages
- Ensure all required Python packages are installed
- Verify the `shared/` directory is accessible

## 📈 Performance Tips

- For large maps, disable grid display (G key) to improve rendering
- Use smaller map sizes for faster editing
- Save frequently to avoid losing work
- Close other applications when editing very large maps
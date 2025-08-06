# Co-op Survival RTS Game

A cooperative survival RTS game, built with Python, Pygame, and FastAPI.

## Architecture

- **Server**: FastAPI with WebSocket support for real-time multiplayer
- **Client**: Pygame-based 2D top-down RTS interface
- **Shared**: Common models and constants used by both server and client

## Project Structure

```
coop_strat/
├── server/           # FastAPI multiplayer server
│   ├── app/         # Main application logic
│   ├── models/      # Data models
│   ├── services/    # Game services (lobby, AI, etc.)
│   └── utils/       # Utility functions
├── client/          # Pygame client
│   ├── scenes/      # Game scenes (menu, game, etc.)
│   ├── ui/          # UI components
│   ├── entities/    # Game entities (heroes, buildings, etc.)
│   └── utils/       # Client utilities
└── shared/          # Shared code between server and client
    ├── models/      # Shared data models
    └── constants/   # Game constants
```

## Getting Started

1. Install dependencies: `pip install -r requirements.txt`
2. Start the server: `python server/main.py`
3. Run the client: `python client/main.py`

## Game Features

- 4 unique hero classes (Tank, Builder, Archer, Mage)
- Procedural map generation with resource placement
- Fog of war exploration system
- Enemy AI with wave-based attacks
- Real-time multiplayer cooperation
- Minimalist 2D graphics optimized for gameplay

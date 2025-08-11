# Agent Guidelines for Co-op Survival RTS

## Build/Test Commands
- **Start Server**: `python server/main.py` or `./start_server.sh`
- **Start Client**: `python client/main.py` or `./start_client.sh`
- **Debug Mode**: `./start_server_debug.sh` and `./start_client_debug.sh`
- **Run Single Test**: `python test_<name>.py` (e.g., `python test_connection.py`)
- **Install Dependencies**: `pip install -r requirements.txt`

## Technology Stack
- **Backend**: FastAPI + WebSockets + Redis
- **Frontend**: Pygame + asyncio
- **Models**: Pydantic for data validation
- **Architecture**: Client-server with shared models

## Code Style
- **Imports**: Standard library first, then third-party, then local (separated by blank lines)
- **Naming**: snake_case for variables/functions, PascalCase for classes, UPPER_CASE for constants
- **Types**: Use type hints with Pydantic models; prefer str Enums over plain strings
- **Async**: Use async/await for network operations; asyncio.create_task() for background tasks
- **Logging**: Use structured logging with logger = logging.getLogger(__name__)
- **Error Handling**: Log errors with exc_info=True; graceful degradation for network issues
- **Structure**: Keep related functionality in services/; shared models in shared/models/

---

## Task Responsibility Matrix

| Task                        | Server Responsibility         | Client Responsibility         | Notes / Agent Guidance                                                                |
|-----------------------------|-------------------------------|-------------------------------|---------------------------------------------------------------------------------------|
| Physics & Collision         | ✅ Authoritative              | Optional local prediction    | Server is source of truth; client may predict for responsiveness, but server corrects |
| AI & NPC Behavior           | ✅ Authoritative              | ❌                           | All AI logic runs on server; client receives updates only.                            |
| Game Rules (damage, win)    | ✅ Authoritative              | ❌                           | Server enforces all rules; client displays results.                                   |
| Player Input Handling       | ✅ Validated                  | ✅ Predicted locally         | Client predicts for responsiveness; server validates and corrects as needed.          |
| Rendering                   | ❌                            | ✅                           | All rendering is client-side only.                                                    |
| Sound Effects               | ❌                            | ✅                           | All sound is client-side only.                                                        |
| UI Logic                    | ❌                            | ✅                           | All UI logic is client-side only.                                                     |

### Agent Assignment Guidance

- **Server Agents**: Implement all authoritative logic (physics, AI, rules, input validation).
- **Client Agents**: Implement prediction, rendering, sound, and UI logic.
- **Shared Models**: Use shared/models/ for data structures passed between server and client.
- **Networking**: Ensure all authoritative decisions are communicated from server to client; client-side predictions must be correctable by server responses.

---

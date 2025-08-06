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
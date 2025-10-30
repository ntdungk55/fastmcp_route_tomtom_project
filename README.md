# FastMCP Route TomTom — Clean Architecture

A Minimal MCP server for route planning with TomTom. Windows-friendly, uses uv, and structured with Clean Architecture.

## Quick Start (Windows)

```powershell
uv sync
uv run python app/interfaces/mcp/server.py
```

Set environment variables (PowerShell):

```powershell
$env:TOMTOM_API_KEY = '<YOUR_TOMTOM_KEY>'
$env:TOMTOM_BASE_URL = 'https://api.tomtom.com'
$env:HTTP_TIMEOUT_SEC = '12'
$env:DATABASE_PATH = 'app/infrastructure/persistence/database/destinations.db'
```

## Tools (MCP)

- get_detailed_route(origin_address, destination_address, travel_mode, country_set?, language?)
- save_destination(name, address)
- list_destinations()
- delete_destination(name?, address?)
- update_destination(destination_id, name?, address?)

Server entrypoint: `app/interfaces/mcp/server.py`.

## Development

```powershell
uv sync --dev
uv run pytest
uv run ruff check .
uv run ruff format .
uv run mypy app
```

## Project Structure

- app/domain — Entities, Value Objects, Enums
- app/application — Use cases, DTOs, Ports
- app/infrastructure — Adapters (TomTom, SQLite), HTTP, logging
- app/interfaces — MCP server

## Notes

- Removed `test_client/` and `client_config_examples/` as unused.
- Auto-generation docs exist; tests for `get_detailed_route` are not created by CI. Add tests under `tests/` as needed.
- See `instructions/INSTRUCTION_UPDATE_2025-10-30.md` for latest changes.

## License

MIT

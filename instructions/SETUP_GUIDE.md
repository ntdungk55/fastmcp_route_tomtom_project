# Setup Guide

This project is an MCP server (TomTom) using Clean Architecture, optimized for Windows and `uv`.

## Requirements
- Python 3.13+
- `uv` package manager — see https://docs.astral.sh/uv/getting-started/installation/
- TomTom API key

## Install
```powershell
uv sync
```

## Run the server
```powershell
# Set environment variables
$env:TOMTOM_API_KEY = '<YOUR_TOMTOM_KEY>'
$env:TOMTOM_BASE_URL = 'https://api.tomtom.com'
$env:HTTP_TIMEOUT_SEC = '12'
$env:DATABASE_PATH = 'app/infrastructure/persistence/database/destinations.db'

# Start the MCP server
uv run python app/interfaces/mcp/server.py
```

## Available MCP Tools
- get_detailed_route(origin_address, destination_address, travel_mode?, country_set?, language?)
- save_destination(name, address)
- list_destinations()
- delete_destination(name?, address?)
- update_destination(destination_id, name?, address?)

## Development
```powershell
uv sync --dev
uv run pytest
uv run ruff check .
uv run ruff format .
uv run mypy app
```

## Project Structure (short)
- app/domain — Entities, Value Objects, Enums
- app/application — Use cases, DTOs, Ports
- app/infrastructure — Adapters (TomTom, SQLite), HTTP, logging
- app/interfaces — MCP server

## Notes
- Default database path: `app/infrastructure/persistence/database/destinations.db`.
- Any `*.db` files at repo root were removed as unused.

# FastMCP Route Server — TomTom (Clean Architecture)

A **MCP** server using **FastMCP** for detailed route planning and destination management via **TomTom API**.
- **Language:** Python 3.13+
- **Run:** `uv` (fast Python package manager)
- **OS:** Windows-friendly
- **Architecture:** Clean Architecture (Domain → Application → Infrastructure → Interfaces) with Ports/Adapters, ACL, DI.

## Quick Start (Windows, with uv)
```powershell
# 0) install uv if needed → https://docs.astral.sh/uv/getting-started/installation/
uv sync
uv run python app/interfaces/mcp/server.py
```

### Configure your MCP client
```json
{
  "mcpServers": {
    "tomtom-route-server": {
      "command": "uv",
      "args": ["run", "python", "D:/Project/Project gennerated by AI/fastmcp_route_tomtom_project/app/interfaces/mcp/server.py"],
      "env": {
        "TOMTOM_BASE_URL": "https://api.tomtom.com",
        "TOMTOM_API_KEY": "<YOUR_TOMTOM_KEY>",
        "HTTP_TIMEOUT_SEC": "12"
      }
    }
  }
}
```

## Available Tools

### 1. **get_detailed_route** ⭐ Primary Tool

Get detailed route with turn-by-turn instructions and traffic information.

**Parameters:**
- `origin_address` (string): Starting address
- `destination_address` (string): Destination address  
- `travel_mode` (string): "car", "bicycle", or "foot" (default: "car")
- `country_set` (string): Country code (default: "VN")
- `language` (string): Language (default: "vi-VN")

Example:
```python
result = await get_detailed_route(
    origin_address="Hồ Gươm, Hà Nội",
    destination_address="Chợ Bến Thành, TP.HCM",
    travel_mode="car"
)
```

Response:
```json
{
  "origin": {"address": "...", "lat": 21.0285, "lon": 105.8542},
  "destination": {"address": "...", "lat": 10.7720, "lon": 106.6986},
  "main_route": {
    "total_distance_meters": 1234567,
    "total_duration_seconds": 45678,
    "traffic_condition": {
      "description": "Traffic delays: 15 minutes",
      "delay_minutes": 15
    },
    "instructions": [...],
    "sections": [...]
  }
}
```

### 2-5. **Destination Management Tools**

- `save_destination(name, address)` - Save a destination for later use
- `list_destinations()` - List all saved destinations
- `delete_destination(name?, address?)` - Delete a destination
- `update_destination(destination_id, name?, address?)` - Update destination info

## Developer Notes

### Architecture
- **Domain Layer**: `app/domain/` - Entities, Value Objects, Enums
- **Application Layer**: `app/application/` - Use Cases, DTOs, Ports
- **Infrastructure Layer**: `app/infrastructure/` - Adapters (TomTom, SQLite)
- **Interface Layer**: `app/interfaces/` - MCP Server

### Key Files
- Port (Interface): `app/application/ports/routing_provider.py`
- Adapter (TomTom): `app/infrastructure/tomtom/adapters/routing_adapter.py`
- ACL mapping: `app/infrastructure/tomtom/acl/mappers.py`
- DI Container: `app/di/container.py`
- MCP Server: `app/interfaces/mcp/server.py`

### Development Commands

Using uv:
```powershell
uv sync --dev          # Install with dev dependencies
uv run pytest         # Run tests
uv run ruff check .   # Lint
uv run ruff format .  # Format
uv run mypy app       # Type check
```

### Environment Variables
- `TOMTOM_BASE_URL` (default: `https://api.tomtom.com`)
- `TOMTOM_API_KEY` (**required**)
- `HTTP_TIMEOUT_SEC` (default: 12)
- `LOG_LEVEL` (default: INFO)
- `DATABASE_PATH` (default: `destinations.db`)

### Windows Debug Tips
- Check env var: `$env:TOMTOM_API_KEY`
- Check port: `netstat -ano | findstr :8081`
- View logs: Server logs show detailed request/response info

## Testing

### Unit Tests
```powershell
uv run pytest tests/unit/
```

### Integration Tests
```powershell
uv run pytest tests/integration/
```

### Test Coverage
```powershell
uv run pytest --cov=app tests/
```

## Clean Architecture Benefits

1. **Testability**: Easy to mock dependencies and test in isolation
2. **Maintainability**: Clear separation of concerns
3. **Flexibility**: Easy to swap adapters (TomTom → Google Maps)
4. **Scalability**: Add new use cases without affecting existing code

## Related Documentation

- [MCP Server Usage Guide](MCP_SERVER_USAGE_GUIDE_Instruction.md) - Detailed tool documentation
- [Clean Architecture Usage](CLEAN_ARCHITECTURE_USAGE_Instruction.md) - Architecture guide
- [FastMCP Client Setup](FASTMCP_CLIENT_SETUP_Instruction.md) - Client configuration


# FastMCP Route Server — TomTom (Clean Architecture)

A minimal **MCP** server using **FastMCP** exposing `calculate_route` via **TomTom Routing API**.
- **Language:** Python 3.11+
- **Run:** `uv` (fast Python package manager)
- **OS:** Windows-friendly
- **Architecture:** Clean Architecture (Domain → Application → Infrastructure → Interfaces) with Ports/Adapters, ACL, DI.

## Quick Start (Windows, with uv)
```powershell
# 0) install uv if needed → https://docs.astral.sh/uv/getting-started/installation/
uv sync
uv run -m interfaces.mcp.server
```

### Configure your MCP client
```json
{
  "mcpServers": {
    "route-mcp": {
      "command": "uv",
      "args": ["run", "-m", "interfaces.mcp.server"],
      "env": {
        "TOMTOM_BASE_URL": "https://api.tomtom.com",
        "TOMTOM_API_KEY": "<YOUR_TOMTOM_KEY>",
        "HTTP_TIMEOUT_SEC": "12"
      }
    }
  }
}
```

### Use the tool
Invoke `calculate_route` with:
- `origin_lat`, `origin_lon`
- `dest_lat`, `dest_lon`
- `travel_mode` in `["car","bicycle","foot"]` (TomTom: `car` | `bicycle` | `pedestrian`)

Example response:
```json
{
  "summary": { "distance_m": 12345, "duration_s": 678 },
  "sections": [
    { "kind": "traffic:JAM", "start_index": 0, "end_index": 0 }
  ]
}
```

## Developer Notes
- Port: `app/application/ports/routing_provider.py`
- Adapter (TomTom): `app/infrastructure/tomtom/adapters/routing_adapter.py`
- ACL mapping: `app/infrastructure/tomtom/acl/mappers.py`
- DI wiring: `app/di/container.py`
- MCP server: `interfaces/mcp/server.py`

### Development Commands

Using Makefile (recommended):
```powershell
make dev-install    # Install with dev dependencies
make test          # Run tests
make test-cov      # Run tests with coverage
make lint          # Lint code
make format        # Format code
make type-check    # Type checking
make check         # Run all checks
make run           # Run MCP server
```

Or using uv directly:
```powershell
uv sync --dev      # Install with dev dependencies
uv run pytest     # Run tests
uv run ruff check . # Lint
uv run ruff format . # Format
uv run mypy app    # Type check
```

### Docker Support

Build and run with Docker:
```powershell
docker build -t fastmcp-route-tomtom .
docker run -e TOMTOM_API_KEY=your_key_here fastmcp-route-tomtom
```

### Env vars
- `TOMTOM_BASE_URL` (default `https://api.tomtom.com`)
- `TOMTOM_API_KEY` (**required**)
- `HTTP_TIMEOUT_SEC` (default 12)
- `LOG_LEVEL` (default INFO)

### Windows debug tips
- Bật venv: `.\.venv\Scriptsctivate` (uv tự quản lý env, nhưng tip hữu ích nếu cần)
- Kiểm tra biến env trong PowerShell: `$env:TOMTOM_API_KEY`
- Kết nối mạng/timeout: điều chỉnh `HTTP_TIMEOUT_SEC`


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

### Lint & Type check
```powershell
uv run ruff check .
uv run ruff format .
uv run mypy app
```

### Env vars
- `TOMTOM_BASE_URL` (default `https://api.tomtom.com`)
- `TOMTOM_API_KEY` (**required**)
- `HTTP_TIMEOUT_SEC` (default 12)

### Windows debug tips
- Bật venv: `.\.venv\Scriptsctivate` (uv tự quản lý env, nhưng tip hữu ích nếu cần)
- Kiểm tra biến env trong PowerShell: `$env:TOMTOM_API_KEY`
- Kết nối mạng/timeout: điều chỉnh `HTTP_TIMEOUT_SEC`

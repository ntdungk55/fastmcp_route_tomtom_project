# Hướng dẫn cài đặt và chạy dự án

Dự án MCP server (TomTom) theo Clean Architecture, chạy tốt trên Windows với `uv`.

## Yêu cầu
- Python 3.13+
- `uv` (trình quản lý gói nhanh): xem hướng dẫn cài đặt tại https://docs.astral.sh/uv/getting-started/installation/
- API key TomTom

## Cài đặt
```powershell
uv sync
```

## Chạy server
```powershell
# Thiết lập biến môi trường
$env:TOMTOM_API_KEY = '<YOUR_TOMTOM_KEY>'
$env:TOMTOM_BASE_URL = 'https://api.tomtom.com'
$env:HTTP_TIMEOUT_SEC = '12'
$env:DATABASE_PATH = 'app/infrastructure/persistence/database/destinations.db'

# Chạy server MCP
uv run python app/interfaces/mcp/server.py
```

## Công cụ MCP có sẵn
- get_detailed_route(origin_address, destination_address, travel_mode, country_set?, language?)
- save_destination(name, address)
- list_destinations()
- delete_destination(name?, address?)
- update_destination(destination_id, name?, address?)

## Phát triển
```powershell
uv sync --dev
uv run pytest
uv run ruff check .
uv run ruff format .
uv run mypy app
```

## Cấu trúc dự án (rút gọn)
- app/domain — Entities, Value Objects, Enums
- app/application — Use cases, DTOs, Ports
- app/infrastructure — Adapters (TomTom, SQLite), HTTP, logging
- app/interfaces — MCP server

## Ghi chú
- Database mặc định: `app/infrastructure/persistence/database/destinations.db`.
- Các file `*.db` ở root đã được xóa vì không dùng.

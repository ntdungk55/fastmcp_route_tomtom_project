# 🚀 Hướng Dẫn Sử Dụng TomTom Route MCP Server

## 📋 Tổng Quan

MCP Server này cung cấp dịch vụ tính toán route chi tiết và quản lý điểm đến sử dụng TomTom API thông qua giao thức MCP (Model Context Protocol).

- **Server Address**: `192.168.1.7:8081`
- **Protocol**: MCP over Streamable HTTP
- **Architecture**: Clean Architecture với Ports & Adapters pattern
- **Available Tools**: 5 tools (route planning + destination management)

## 🛠️ Cài Đặt và Chạy Server

### 1. Chuẩn Bị Môi Trường

```bash
# Clone project và cài đặt dependencies
cd fastmcp_route_tomtom_project

# Cài đặt dependencies với uv
uv sync
```

### 2. Cấu Hình Environment Variables

Tạo file `.env` hoặc set environment variables:

```bash
# Windows PowerShell
$env:TOMTOM_API_KEY="your_tomtom_api_key_here"
$env:TOMTOM_BASE_URL="https://api.tomtom.com"
$env:HTTP_TIMEOUT_SEC="12"
$env:LOG_LEVEL="INFO"

# Linux/Mac
export TOMTOM_API_KEY="your_tomtom_api_key_here"
export TOMTOM_BASE_URL="https://api.tomtom.com"
export HTTP_TIMEOUT_SEC="12"
export LOG_LEVEL="INFO"
```

### 3. Khởi Động Server

```bash
# Chạy trực tiếp
uv run python app/interfaces/mcp/server.py

# Hoặc sử dụng start script
uv run python start_server.py
```

Server sẽ khởi động tại: `http://192.168.1.7:8081`

## 🔌 Kết Nối MCP Client

### Cấu Hình Claude Desktop

Thêm vào file `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "tomtom-route-server": {
      "command": "uv",
      "args": ["run", "python", "D:/Project/Project gennerated by AI/fastmcp_route_tomtom_project/start_server.py"],
      "env": {
        "TOMTOM_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

## 🧰 Available Tools

### 1. **get_detailed_route** ⭐

Tính toán route chi tiết với turn-by-turn instructions và traffic information.

**Parameters:**
- `origin_address` (string): Địa chỉ xuất phát
- `destination_address` (string): Địa chỉ đến
- `travel_mode` (string): Phương tiện ("car", "bicycle", "foot") - mặc định: "car"
- `country_set` (string): Mã quốc gia - mặc định: "VN"
- `language` (string): Ngôn ngữ - mặc định: "vi-VN"

**Ví dụ sử dụng:**

```python
result = await get_detailed_route(
    origin_address="Hồ Gươm, Hoàn Kiếm, Hà Nội",
    destination_address="Chợ Bến Thành, Quận 1, TP.HCM",
    travel_mode="car"
)
```

**Response format:**
```json
{
  "origin": {
    "address": "Hồ Gươm, Hoàn Kiếm, Hà Nội",
    "name": "Hồ Gươm",
    "lat": 21.0285,
    "lon": 105.8542
  },
  "destination": {
    "address": "Chợ Bến Thành, Quận 1, TP.HCM",
    "name": "Chợ Bến Thành",
    "lat": 10.7720,
    "lon": 106.6986
  },
  "main_route": {
    "summary": "Route via car",
    "total_distance_meters": 1234567,
    "total_duration_seconds": 45678,
    "traffic_condition": {
      "description": "Traffic delays: 15 minutes, 3 sections affected",
      "delay_minutes": 15
    },
    "instructions": [
      {
        "step": 1,
        "instruction": "Bắt đầu từ điểm xuất phát",
        "distance_meters": 500,
        "duration_seconds": 120,
        "traffic_condition": null
      }
    ],
    "sections": [
      {
        "type": "traffic",
        "start_address": "Đường ABC, Quận X",
        "end_address": "Đường XYZ, Quận Y",
        "delay_seconds": 300,
        "magnitude": 2,
        "coordinates": {
          "start": {"lat": 10.77, "lon": 106.69},
          "end": {"lat": 10.78, "lon": 106.70}
        }
      }
    ]
  },
  "alternative_routes": [],
  "travel_mode": "car",
  "total_alternative_count": 0
}
```

### 2. **save_destination**

Lưu điểm đến vào database để sử dụng lại sau này.

**Parameters:**
- `name` (string): Tên điểm đến
- `address` (string): Địa chỉ điểm đến

**Ví dụ:**

```python
result = await save_destination(
    name="Văn phòng",
    address="123 Lê Lợi, Quận 1, TP.HCM"
)
```

**Response:**
```json
{
  "success": true,
  "message": "Destination 'Văn phòng' saved successfully",
  "destination_id": "uuid-here",
  "error": null
}
```

### 3. **list_destinations**

Liệt kê tất cả điểm đến đã lưu.

**Parameters:** Không có

**Ví dụ:**

```python
result = await list_destinations()
```

**Response:**
```json
{
  "success": true,
  "destinations": [
    {
      "id": "uuid-1",
      "name": "Văn phòng",
      "address": "123 Lê Lợi, Quận 1, TP.HCM",
      "lat": 10.7720,
      "lon": 106.6986,
      "created_at": "2025-01-15T10:30:00",
      "updated_at": "2025-01-15T10:30:00"
    }
  ],
  "total_count": 1,
  "error": null
}
```

### 4. **delete_destination**

Xóa điểm đến đã lưu.

**Parameters:**
- `name` (string, optional): Tên điểm đến cần xóa
- `address` (string, optional): Địa chỉ điểm đến cần xóa

**Lưu ý:** Phải cung cấp ít nhất một trong hai: name hoặc address

**Ví dụ:**

```python
result = await delete_destination(name="Văn phòng")
```

**Response:**
```json
{
  "success": true,
  "message": "Destination deleted successfully",
  "error": null
}
```

### 5. **update_destination**

Cập nhật thông tin điểm đến.

**Parameters:**
- `destination_id` (string): ID của điểm đến
- `name` (string, optional): Tên mới
- `address` (string, optional): Địa chỉ mới

**Lưu ý:** Phải cung cấp ít nhất một trong hai: name hoặc address

**Ví dụ:**

```python
result = await update_destination(
    destination_id="uuid-here",
    name="Văn phòng mới",
    address="456 Nguyễn Huệ, Quận 1, TP.HCM"
)
```

**Response:**
```json
{
  "success": true,
  "message": "Destination updated successfully",
  "destination_id": "uuid-here",
  "error": null
}
```

## 🔍 Testing và Debug

### 1. Kiểm Tra Server Health

```bash
# Check if server is running
curl http://192.168.1.7:8081
```

### 2. Test với Python Client

```python
import asyncio
from app.di.container import Container

async def test():
    container = Container()
    await container.initialize_database()
    
    # Test get_detailed_route
    result = await container.get_detailed_route.execute(
        DetailedRouteRequest(
            origin_address="Hồ Gươm, Hà Nội",
            destination_address="Chợ Bến Thành, TP.HCM",
            travel_mode="car"
        )
    )
    print(result)

asyncio.run(test())
```

## 📊 Kiến Trúc

Server được xây dựng theo **Clean Architecture**:

- **Domain Layer**: Entities, Value Objects, Enums
- **Application Layer**: Use Cases, DTOs, Ports (interfaces)
- **Infrastructure Layer**: Adapters (TomTom API, SQLite Database)
- **Interface Layer**: MCP Server (FastMCP)

### Dependency Injection

Tất cả dependencies được quản lý bởi DI Container:
- Adapters tự động inject vào Use Cases
- Repository tự động inject vào Use Cases
- Configuration tự động load từ environment variables

## 🐛 Troubleshooting

### Server không khởi động

1. Kiểm tra API key:
```bash
echo $TOMTOM_API_KEY  # Linux/Mac
echo $env:TOMTOM_API_KEY  # Windows
```

2. Kiểm tra port 8081 có bị chiếm:
```bash
netstat -ano | findstr :8081  # Windows
lsof -i :8081  # Linux/Mac
```

### Tool không trả về kết quả

1. Kiểm tra logs:
   - Server logs sẽ hiển thị chi tiết request/response
   - Tìm các dòng `[ERROR]` hoặc `[WARNING]`

2. Kiểm tra địa chỉ hợp lệ:
   - Địa chỉ phải đủ chi tiết để geocoding thành công
   - Thêm thành phố/quốc gia nếu cần

### Traffic sections không có dữ liệu

- Traffic data chỉ có sẵn tại các vị trí có sensor của TomTom
- Một số tuyến đường có thể không có dữ liệu traffic real-time

## 📝 Notes

- Server sử dụng SQLite database để lưu trữ destinations tại `destinations.db`
- Tất cả API calls đều có timeout 12 seconds
- Logs được lưu với format JSON structure
- Server hỗ trợ async/await cho tất cả operations

## 🔗 Related Documentation

- [Clean Architecture Usage Guide](CLEAN_ARCHITECTURE_USAGE_Instruction.md)
- [FastMCP Client Setup](FASTMCP_CLIENT_SETUP_Instruction.md)
- [Integrated Flow README](INTEGRATED_FLOW_README.md)

# 🚀 FastMCP Client Setup Guide - Clean Architecture v5

## 📋 Cấu hình MCP Client cho TomTom Route Server

### 1. **Claude Desktop Configuration**

Thêm vào file cấu hình Claude Desktop (`%APPDATA%\Claude\claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "tomtom-route-fastmcp": {
      "command": "uv",
      "args": ["run", "python", "start_server.py"],
      "env": {
        "TOMTOM_API_KEY": "Que13lcTfAXXY2gC4rL84KuDh6ZCQUxZ",
        "TOMTOM_BASE_URL": "https://api.tomtom.com",
        "HTTP_TIMEOUT_SEC": "12",
        "LOG_LEVEL": "INFO",
        "DATABASE_PATH": "app/infrastructure/persistence/database/destinations.db"
      }
    }
  }
}
```

### 2. **VS Code MCP Configuration**

Thêm vào file cấu hình VS Code MCP:

```json
{
  "mcpServers": {
    "tomtom-route-fastmcp": {
      "command": "uv",
      "args": ["run", "python", "start_server.py"],
      "env": {
        "TOMTOM_API_KEY": "Que13lcTfAXXY2gC4rL84KuDh6ZCQUxZ",
        "TOMTOM_BASE_URL": "https://api.tomtom.com",
        "HTTP_TIMEOUT_SEC": "12",
        "LOG_LEVEL": "INFO",
        "DATABASE_PATH": "app/infrastructure/persistence/database/destinations.db"
      }
    }
  }
}
```

### 3. **HTTP Client Configuration**

Nếu client hỗ trợ HTTP MCP:

```json
{
  "mcpServers": {
    "tomtom-route-http": {
      "type": "http",
      "url": "http://localhost:8081/mcp",
      "headers": {
        "Content-Type": "application/json"
      },
      "timeout": 30000
    }
  }
}
```

## 🛠️ Available Tools

### **Routing Tools**
- `calculate_route` - Tính toán route từ điểm xuất phát đến điểm đích
- `get_via_route` - Tính toán route qua các điểm trung gian

### **Geocoding Tools**  
- `geocode_address` - Chuyển đổi địa chỉ thành tọa độ
- `get_intersection_position` - Lấy vị trí giao lộ
- `get_street_center` - Lấy trung tâm đường phố

### **Traffic Tools**
- `get_traffic_condition` - Lấy thông tin tình trạng giao thông
- `analyze_route_traffic` - Phân tích giao thông trên route
- `check_address_traffic` - Kiểm tra giao thông tại địa chỉ

### **Destination Management Tools**
- `save_destination` - Lưu điểm đến yêu thích
- `list_destinations` - Liệt kê các điểm đến đã lưu
- `update_destination` - Cập nhật thông tin điểm đến
- `delete_destination` - Xóa điểm đến

### **Example Usage:**
```json
{
  "name": "calculate_route",
  "arguments": {
    "origin_lat": 40.7128,
    "origin_lon": -74.0060,
    "dest_lat": 40.7589,
    "dest_lon": -73.9851,
    "travel_mode": "car"
  }
}
```

## 🔧 Server Endpoints

- **Health Check**: `GET http://localhost:8081/health`
- **List Tools**: `GET http://localhost:8081/tools/list`
- **Calculate Route**: `POST http://localhost:8081/calculate_route`
- **MCP Protocol**: `POST http://localhost:8081/mcp`

## 🚀 Quick Start

1. **Chạy server:**
   ```powershell
   $env:TOMTOM_API_KEY="Que13lcTfAXXY2gC4rL84KuDh6ZCQUxZ"; uv run python start_server.py
   ```

2. **Test server:**
   ```powershell
   Invoke-WebRequest -Uri "http://localhost:8081/health" -Method GET -UseBasicParsing
   ```

3. **Cấu hình client** với JSON settings ở trên

## 🏗️ Clean Architecture Features

- **Domain Layer**: Business entities và value objects
- **Application Layer**: Use cases và DTOs
- **Infrastructure Layer**: Database, HTTP clients, external APIs
- **Interfaces Layer**: MCP server implementation
- **Dependency Injection**: Container quản lý dependencies
- **Database**: SQLite với migrations tự động

## 📝 Notes

- Server sử dụng Clean Architecture v5 với FastMCP framework
- Database files được lưu trong `app/infrastructure/persistence/database/`
- Hỗ trợ cả stdio và HTTP protocols
- API key TomTom đã được cấu hình sẵn
- Tự động khởi tạo database và migrations

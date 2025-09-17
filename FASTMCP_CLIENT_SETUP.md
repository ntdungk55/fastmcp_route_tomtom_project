# 🚀 FastMCP Client Setup Guide

## 📋 Cấu hình MCP Client cho TomTom Route Server

### 1. **Claude Desktop Configuration**

Thêm vào file cấu hình Claude Desktop (`%APPDATA%\Claude\claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "tomtom-route-fastmcp": {
      "command": "uv",
      "args": ["run", "python", "start_http_server.py"],
      "env": {
        "TOMTOM_API_KEY": "Que13lcTfAXXY2gC4rL84KuDh6ZCQUxZ",
        "TOMTOM_BASE_URL": "https://api.tomtom.com",
        "HTTP_TIMEOUT_SEC": "12",
        "LOG_LEVEL": "INFO",
        "SERVER_HOST": "192.168.1.3",
        "SERVER_PORT": "8081"
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
      "args": ["run", "python", "start_http_server.py"],
      "env": {
        "TOMTOM_API_KEY": "Que13lcTfAXXY2gC4rL84KuDh6ZCQUxZ",
        "TOMTOM_BASE_URL": "https://api.tomtom.com",
        "HTTP_TIMEOUT_SEC": "12",
        "LOG_LEVEL": "INFO",
        "SERVER_HOST": "192.168.1.3",
        "SERVER_PORT": "8081"
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
      "url": "http://192.168.1.3:8081/mcp",
      "headers": {
        "Content-Type": "application/json"
      },
      "timeout": 30000
    }
  }
}
```

## 🛠️ Available Tools

### `calculate_route`
Tính toán route từ điểm xuất phát đến điểm đích sử dụng TomTom API.

**Parameters:**
- `origin_lat` (number): Vĩ độ điểm xuất phát
- `origin_lon` (number): Kinh độ điểm xuất phát  
- `dest_lat` (number): Vĩ độ điểm đích
- `dest_lon` (number): Kinh độ điểm đích
- `travel_mode` (string): Chế độ di chuyển - "car", "bicycle", "foot" (mặc định: "car")

**Example Usage:**
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

- **Health Check**: `GET http://192.168.1.3:8081/health`
- **List Tools**: `GET http://192.168.1.3:8081/tools/list`
- **Calculate Route**: `POST http://192.168.1.3:8081/calculate_route`
- **MCP Protocol**: `POST http://192.168.1.3:8081/mcp`

## 🚀 Quick Start

1. **Chạy server:**
   ```powershell
   $env:TOMTOM_API_KEY="Que13lcTfAXXY2gC4rL84KuDh6ZCQUxZ"; uv run python start_http_server.py
   ```

2. **Test server:**
   ```powershell
   Invoke-WebRequest -Uri "http://192.168.1.3:8081/health" -Method GET -UseBasicParsing
   ```

3. **Cấu hình client** với JSON settings ở trên

## 📝 Notes

- Server sử dụng FastMCP framework
- Tự động retry port nếu port mặc định bị chiếm
- Hỗ trợ cả stdio và HTTP protocols
- API key TomTom đã được cấu hình sẵn

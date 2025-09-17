# 🚀 Hướng Dẫn Sử Dụng TomTom Route MCP Server

## 📋 Tổng Quan

MCP Server này cung cấp dịch vụ tính toán route sử dụng TomTom Routing API thông qua giao thức MCP (Model Context Protocol).

- **Server Address**: `192.168.1.3:8081`
- **Protocol**: MCP over HTTP/WebSocket
- **Available Tools**: `calculate_route`

## 🛠️ Cài Đặt và Chạy Server

### 1. Chuẩn Bị Môi Trường

```bash
# Clone project và cài đặt dependencies
git clone <your-repo-url>
cd fastmcp_route_tomtom_project

# Cài đặt dependencies
uv sync --dev
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
# Sử dụng Makefile (khuyến nghị)
make start-server

# Hoặc chạy trực tiếp
uv run start_server.py

# Hoặc sử dụng Python
python start_server.py
```

Server sẽ khởi động tại: `http://192.168.1.3:8081`

## 🔌 Kết Nối MCP Client

### 1. Cấu Hình MCP Client (Claude Desktop/VS Code)

Thêm vào file cấu hình MCP client:

```json
{
  "mcpServers": {
    "tomtom-route-server": {
      "command": "python",
      "args": ["/path/to/your/project/start_server.py"],
      "env": {
        "TOMTOM_API_KEY": "your_api_key_here",
        "TOMTOM_BASE_URL": "https://api.tomtom.com",
        "HTTP_TIMEOUT_SEC": "12",
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```

### 2. Kết Nối Remote MCP Client

Nếu client chạy trên máy khác, sử dụng:

```json
{
  "mcpServers": {
    "tomtom-route-remote": {
      "transport": {
        "type": "http",
        "host": "192.168.1.3",
        "port": 8081
      }
    }
  }
}
```

## 🧰 Sử Dụng Tools

### Tool: `calculate_route`

Tính toán route từ điểm A đến điểm B với thông tin traffic.

**Parameters:**
- `origin_lat` (float): Vĩ độ điểm xuất phát
- `origin_lon` (float): Kinh độ điểm xuất phát  
- `dest_lat` (float): Vĩ độ điểm đến
- `dest_lon` (float): Kinh độ điểm đến
- `travel_mode` (string): Phương tiện di chuyển ("car", "bicycle", "foot")

**Ví dụ sử dụng:**

```python
# Từ Hồ Gươm đến Chợ Bến Thành
result = await calculate_route(
    origin_lat=21.0285,
    origin_lon=105.8542,
    dest_lat=10.7720,
    dest_lon=106.6986,
    travel_mode="car"
)
```

**Response format:**
```json
{
  "summary": {
    "distance_m": 1234567,
    "duration_s": 45678
  },
  "sections": [
    {
      "kind": "traffic:JAM",
      "start_index": 0,
      "end_index": 10
    }
  ]
}
```

## 🔍 Testing và Debug

### 1. Kiểm Tra Server Health

```bash
# Test server accessibility
curl -X GET http://192.168.1.3:8081/health

# Test MCP capabilities
curl -X POST http://192.168.1.3:8081/mcp \
  -H "Content-Type: application/json" \
  -d '{"method": "tools/list", "params": {}}'
```

### 2. Test Tool Functionality

```bash
# Test calculate_route tool
curl -X POST http://192.168.1.3:8081/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "method": "tools/call",
    "params": {
      "name": "calculate_route",
      "arguments": {
        "origin_lat": 21.0285,
        "origin_lon": 105.8542,
        "dest_lat": 10.7720,
        "dest_lon": 106.6986,
        "travel_mode": "car"
      }
    }
  }'
```

## 🚨 Troubleshooting

### 1. Server Không Khởi Động

```bash
# Kiểm tra port có bị sử dụng không
netstat -an | findstr :8081    # Windows
lsof -i :8081                  # Linux/Mac

# Kiểm tra API key
echo $TOMTOM_API_KEY           # Linux/Mac
echo $env:TOMTOM_API_KEY       # Windows
```

### 2. Connection Refused

- Đảm bảo firewall cho phép port 8081
- Kiểm tra network connectivity đến 192.168.1.3
- Verify server đang chạy: `ps aux | grep python`

### 3. API Errors

- Kiểm tra TomTom API key hợp lệ
- Verify network access đến api.tomtom.com
- Check logs để xem error details

## 📝 Logs và Monitoring

Server logs sẽ hiển thị:
- Server startup information
- API requests/responses
- Error details
- Performance metrics

```bash
# Xem logs real-time
tail -f server.log

# Filter error logs
grep ERROR server.log
```

## 🔧 Advanced Configuration

### Custom Host/Port

Sửa file `start_server.py`:

```python
# Thay đổi host/port
mcp.run(host="0.0.0.0", port=9000)
```

### Environment-specific Settings

Tạo file `.env.production`:

```env
TOMTOM_BASE_URL=https://api.tomtom.com
HTTP_TIMEOUT_SEC=30
LOG_LEVEL=WARNING
```

## 📚 Tài Liệu Tham Khảo

- [FastMCP Documentation](https://github.com/jlowin/fastmcp)
- [TomTom Routing API](https://developer.tomtom.com/routing-api/documentation)
- [MCP Protocol Specification](https://modelcontextprotocol.io/)

## 🤝 Hỗ Trợ

Nếu gặp vấn đề:
1. Kiểm tra logs server
2. Verify network connectivity
3. Test với Postman collection trong `resources/`
4. Tạo GitHub issue với error details

---

**Happy Routing! 🗺️**

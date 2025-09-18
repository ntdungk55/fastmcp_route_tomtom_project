# TomTom Route MCP Test Client

Test clients cho TomTom Route MCP Server với Clean Architecture.

## 🚀 Quick Start

### Node.js Client (Original)
```bash
# Install dependencies
npm install

# Run test (default: http://192.168.1.3:8081/mcp)
npm test

# Or run with custom server URL
node test_client.js http://localhost:8081/mcp
```

### Python Client (Clean Architecture)
```bash
# Cần có Python 3.11+ và dependencies
pip install httpx

# Run test cho Clean Architecture server
python test_clean_server.py
```

## 🧪 Tests Available

### Node.js Client (`test_client.js`)
1. **Health Check** - Test server health endpoint
2. **Tools List** - List available MCP tools
3. **Route Calculation** - Test route calculation functionality
4. **MCP Protocol** - Test full MCP protocol compliance

### Python Client (`test_clean_server.py`)
1. **Architecture Compliance** - Kiểm tra Clean Architecture structure
2. **Initialize & Tools List** - Test MCP protocol initialization
3. **Use Cases Testing** - Test từng Use Case riêng biệt
4. **Dependency Injection** - Verify Container wiring
5. **Error Handling** - Test exception handling

## 📋 Example Output

```
🚀 TomTom Route MCP Client Test Suite
📍 Server URL: http://192.168.1.3:8081/mcp
============================================================

🏥 Testing server health...
   Health status: healthy
   API Key configured: ✅

🛠️ Testing tools list...
📤 Sending simple request: tools/list
📥 Response: {
  "tools": [
    {
      "name": "calculate_route",
      "description": "Calculate route from origin to destination using TomTom API"
    }
  ]
}

🗺️ Testing route calculation...
📤 Sending simple request: tools/call
   Params: {
     "name": "calculate_route",
     "arguments": {
       "origin_lat": 21.0285,
       "origin_lon": 105.8542,
       "dest_lat": 10.772,
       "dest_lon": 106.6986,
       "travel_mode": "car"
     }
   }
📥 Response: {
  "result": {
    "success": true,
    "data": {
      "summary": {
        "distance_m": 1234567,
        "duration_s": 45678
      },
      "sections": [...]
    }
  }
}

🎉 All tests completed!
```

## 🔧 Configuration

- **Default Server**: `http://192.168.1.3:8081/mcp`
- **Protocol**: HTTP with JSON requests
- **Format**: MCP protocol 2024-11-05
- **Environment**: Cần `TOMTOM_API_KEY` environment variable

## 📚 Dependencies

### Node.js Client
- `@modelcontextprotocol/sdk`: MCP SDK (for reference)
- `node-fetch`: HTTP requests
- `@types/node`: TypeScript definitions

### Python Client
- `httpx`: Async HTTP client
- `asyncio`: Async support
- `json`: JSON handling

## 🏗️ Testing Clean Architecture

Python client đặc biệt test các aspect của Clean Architecture:

- **Layer Separation**: Verify dependencies chỉ đi một chiều
- **Use Cases**: Test business logic isolation
- **Ports & Adapters**: Verify interface compliance
- **Dependency Injection**: Test Container wiring
- **Domain Independence**: Verify vendor independence

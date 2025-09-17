# TomTom Route MCP Test Client

Simple Node.js client to test the TomTom Route MCP Server functionality.

## 🚀 Quick Start

```bash
# Install dependencies
npm install

# Run test (default: http://192.168.1.3:8081/mcp)
npm test

# Or run with custom server URL
node test_client.js http://localhost:8081/mcp
```

## 🧪 Tests Performed

1. **Health Check** - Test server health endpoint
2. **Tools List** - List available MCP tools
3. **Route Calculation** - Test route calculation functionality
4. **MCP Protocol** - Test full MCP protocol compliance

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
- **Format**: Both simple and MCP protocol formats

## 📚 Dependencies

- `@modelcontextprotocol/sdk`: MCP SDK (for reference)
- `node-fetch`: HTTP requests
- `@types/node`: TypeScript definitions

"""
MCP Server constants cho Interface layer.
"""
from typing import Dict, List


class MCPServerConstants:
    """MCP Server configuration constants."""
    # Server info
    SERVER_NAME = "RouteMCP_TomTom_CleanArch"
    SERVER_VERSION = "1.0.0"
    DESCRIPTION = "TomTom Route MCP Server with Clean Architecture"
    
    # Default server settings
    DEFAULT_HOST = "192.168.1.3"
    DEFAULT_PORT = 8081
    DEFAULT_TRANSPORT = "streamable-http"
    
    # Protocol settings
    MCP_PROTOCOL_VERSION = "2024-11-05"
    JSONRPC_VERSION = "2.0"
    
    # Tool categories
    ROUTING_TOOLS = ["calculate_route"]
    GEOCODING_TOOLS = ["geocode_address", "get_intersection_position", "get_street_center_position"]
    TRAFFIC_TOOLS = ["get_traffic_condition", "get_route_with_traffic", "analyze_route_traffic"]
    COMPOSITE_TOOLS = ["get_via_route", "check_traffic_between_addresses"]


class MCPToolDescriptions:
    """MCP Tool descriptions."""
    CALCULATE_ROUTE = "Tính toán tuyến đường cơ bản từ điểm A đến điểm B"
    GEOCODE_ADDRESS = "Chuyển đổi địa chỉ thành tọa độ GPS"
    GET_INTERSECTION_POSITION = "Tìm tọa độ giao lộ giữa các đường phố"
    GET_STREET_CENTER_POSITION = "Tìm tọa độ trung tâm của một đường phố"
    GET_TRAFFIC_CONDITION = "Lấy thông tin tình trạng giao thông tại một vị trí"
    GET_ROUTE_WITH_TRAFFIC = "Tính toán tuyến đường có kèm thông tin giao thông"
    GET_VIA_ROUTE = "Tính toán tuyến đường qua điểm trung gian A → B → C"
    ANALYZE_ROUTE_TRAFFIC = "Phân tích tình trạng giao thông trên tuyến đường"
    CHECK_TRAFFIC_BETWEEN_ADDRESSES = "Kiểm tra tình trạng giao thông giữa các địa chỉ"


class MCPErrorMessages:
    """MCP Error messages."""
    # Server errors
    SERVER_STARTUP_ERROR = "❌ Error starting server: {error}"
    CONFIG_ERROR = "❌ Configuration error: {error}"
    API_KEY_MISSING = "❌ TOMTOM_API_KEY environment variable is required!"
    
    # Tool errors
    TOOL_EXECUTION_ERROR = "Tool execution failed: {error}"
    INVALID_PARAMETERS = "Invalid parameters: {error}"
    VALIDATION_ERROR = "Validation error: {error}"
    
    # Request errors
    REQUEST_VALIDATION_FAILED = "Request validation failed: {error}"
    UNSUPPORTED_METHOD = "Unsupported method: {method}"
    MALFORMED_REQUEST = "Malformed request: {error}"


class MCPSuccessMessages:
    """MCP Success messages."""
    SERVER_STARTED = "🚀 TomTom MCP Server started successfully"
    SERVER_STOPPED = "👋 Server stopped by user"
    API_KEY_CONFIGURED = "✅ TomTom API key configured"
    TOOL_EXECUTED = "✅ Tool executed successfully: {tool_name}"


class MCPLogMessages:
    """MCP Log messages."""
    # Startup messages
    STARTUP_BANNER = """
🚀 TomTom MCP Server - Clean Architecture
{"=" * 60}
📋 Architecture: Clean Architecture (Hexagonal)
🏗️  Pattern: Ports & Adapters
🔌 Dependency Injection: Container pattern
🛠️  Available tools: {tool_count}
{"=" * 60}
🌐 Transport: {transport}
📡 Endpoint: http://{host}:{port}
{"=" * 60}
"""
    
    TOOL_LIST = """🛠️  Available tools:
   • calculate_route - Tính toán tuyến đường cơ bản
   • geocode_address - Chuyển địa chỉ thành tọa độ
   • get_intersection_position - Tìm tọa độ giao lộ
   • get_street_center_position - Tìm trung tâm đường phố
   • get_traffic_condition - Lấy thông tin giao thông
   • get_route_with_traffic - Tuyến đường có traffic
   • get_via_route - Tuyến đường qua điểm trung gian
   • analyze_route_traffic - Phân tích traffic tuyến đường
   • check_traffic_between_addresses - Kiểm tra traffic giữa địa chỉ"""
    
    # API key setup instructions
    API_KEY_SETUP = """Please set your TomTom API key:
  Windows: $env:TOMTOM_API_KEY='your_api_key_here'
  Linux/Mac: export TOMTOM_API_KEY='your_api_key_here'"""

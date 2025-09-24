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
    
    # Tool categories - sử dụng constants từ MCPToolNames
    ROUTING_TOOLS = ["calculate_route"]
    GEOCODING_TOOLS = ["geocode_address", "get_intersection_position", "get_street_center_position"]
    TRAFFIC_TOOLS = ["get_traffic_condition", "get_route_with_traffic", "analyze_route_traffic"]
    COMPOSITE_TOOLS = ["get_via_route", "check_traffic_between_addresses", "get_detailed_route"]
    DESTINATION_TOOLS = ["save_destination", "list_destinations", "delete_destination", "update_destination"]


class MCPTypeConstants:
    """MCP Type constants for Literal types - sử dụng constants từ Domain layer."""
    # Import constants from Domain layer để tránh duplicate
    from app.domain.constants.api_constants import TravelModeConstants
    
    # Travel mode values for Literal type - sử dụng constants từ Domain
    TRAVEL_MODE_CAR = TravelModeConstants.CAR
    TRAVEL_MODE_BICYCLE = TravelModeConstants.BICYCLE
    TRAVEL_MODE_FOOT = TravelModeConstants.FOOT
    
    # Create list for Literal type
    TRAVEL_MODE_VALUES = [TRAVEL_MODE_CAR, TRAVEL_MODE_BICYCLE, TRAVEL_MODE_FOOT]


class MCPToolNames:
    """MCP Tool names constants."""
    CALCULATE_ROUTE = "calculate_route"
    GEOCODE_ADDRESS = "geocode_address"
    GET_ROUTE_WITH_TRAFFIC = "get_route_with_traffic"
    GET_INTERSECTION_POSITION = "get_intersection_position"
    GET_STREET_CENTER_POSITION = "get_street_center_position"
    GET_TRAFFIC_CONDITION = "get_traffic_condition"
    GET_VIA_ROUTE = "get_via_route"
    ANALYZE_ROUTE_TRAFFIC = "analyze_route_traffic"
    CHECK_TRAFFIC_BETWEEN_ADDRESSES = "check_traffic_between_addresses"
    SAVE_DESTINATION = "save_destination"
    LIST_DESTINATIONS = "list_destinations"
    DELETE_DESTINATION = "delete_destination"
    UPDATE_DESTINATION = "update_destination"
    GET_DETAILED_ROUTE = "get_detailed_route"


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
    GET_DETAILED_ROUTE = "Tính toán tuyến đường chi tiết và cung cấp chỉ dẫn từng bước di chuyển giữa hai địa chỉ, bao gồm hướng dẫn lái xe, khoảng cách, thời gian và thông tin giao thông"
    SAVE_DESTINATION = "Lưu điểm đến với geocoding tự động"
    LIST_DESTINATIONS = "Liệt kê tất cả điểm đến đã lưu"
    DELETE_DESTINATION = "Xóa điểm đến theo ID"
    UPDATE_DESTINATION = "Cập nhật thông tin điểm đến"


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


class MCPToolErrorMessages:
    """MCP Tool specific error messages."""
    # Calculate route errors
    INVALID_COORDINATES = "Invalid coordinates: {error}"
    
    # Geocoding errors
    GEOCODING_FAILED = "Geocoding failed: {error}"
    
    # Route errors
    ROUTE_WITH_TRAFFIC_FAILED = "Route with traffic calculation failed: {error}"
    VIA_ROUTE_FAILED = "Via route calculation failed: {error}"
    GET_DETAILED_ROUTE_FAILED = "Get detailed route failed: {error}"
    
    # Position lookup errors
    INTERSECTION_LOOKUP_FAILED = "Intersection lookup failed: {error}"
    STREET_CENTER_LOOKUP_FAILED = "Street center lookup failed: {error}"
    
    # Traffic errors
    TRAFFIC_CONDITION_FAILED = "Traffic condition lookup failed: {error}"
    TRAFFIC_ANALYSIS_FAILED = "Traffic analysis failed: {error}"
    ADDRESS_TRAFFIC_CHECK_FAILED = "Address traffic check failed: {error}"
    
    # Destination errors
    SAVE_DESTINATION_FAILED = "Save destination failed: {error}"
    LIST_DESTINATIONS_FAILED = "List destinations failed: {error}"
    DELETE_DESTINATION_FAILED = "Delete destination failed: {error}"
    UPDATE_DESTINATION_FAILED = "Update destination failed: {error}"


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


class MCPDetailedRouteLogMessages:
    """MCP Detailed Route Log messages."""
    # Response logging
    SERVER_RESPONSE_HEADER = "\n🔍 MCP Server Response for get_detailed_route:"
    DISTANCE_LOG = "📏 Distance: {distance:,} meters"
    DURATION_LOG = "⏱️ Duration: {duration:,} seconds"
    GUIDANCE_INSTRUCTIONS_LOG = "🧭 Guidance instructions: {count}"
    ROUTE_LEGS_LOG = "🦵 Route legs: {count}"
    ORIGIN_LOG = "📍 Origin: {address}"
    DESTINATION_LOG = "📍 Destination: {address}"
    
    # Guidance instructions logging
    GUIDANCE_HEADER = "\n🧭 First 3 Guidance Instructions:"
    GUIDANCE_STEP = "  {step}. {instruction}"
    GUIDANCE_DISTANCE_DURATION = "     Distance: {distance}m, Duration: {duration}s"
    GUIDANCE_MANEUVER = "     Maneuver: {maneuver}"
    GUIDANCE_ROAD = "     Road: {road_name}"
    GUIDANCE_POINT = "     Point: ({lat}, {lon})"
    
    # Final response logging
    FINAL_RESPONSE_HEADER = "\n📤 Final MCP Response:"
    SUMMARY_LOG = "   Summary: {summary}"
    ROUTE_INSTRUCTIONS_COUNT = "   Route instructions count: {count}"
    ROUTE_LEGS_COUNT = "   Route legs count: {count}"
    TRAFFIC_SECTIONS_COUNT = "   Traffic sections count: {count}"
    
    # Route instructions logging
    ROUTE_INSTRUCTIONS_HEADER = "\n🛣️ First 3 Route Instructions:"
    ROUTE_STEP = "   Step {step}: {instruction}"
    ROUTE_DISTANCE_DURATION = "   Distance: {distance}m, Duration: {duration}s"
    ROUTE_MANEUVER = "   Maneuver: {maneuver}"
    ROUTE_ROAD = "   Road: {road_name}"
    
    # Error logging
    ERROR_HEADER = "\n❌ Error in get_detailed_route: {error}"

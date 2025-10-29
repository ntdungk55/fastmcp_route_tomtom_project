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
    DEFAULT_HOST = "192.168.1.2"
    DEFAULT_PORT = 8081
    DEFAULT_TRANSPORT = "streamable-http"
    
    # Protocol settings
    MCP_PROTOCOL_VERSION = "2024-11-05"
    JSONRPC_VERSION = "2.0"
    
    # Tool categories - use constants from MCPToolNames
    ROUTING_TOOLS = ["calculate_route"]
    GEOCODING_TOOLS = ["geocode_address", "get_intersection_position", "get_street_center_position"]
    TRAFFIC_TOOLS = ["get_traffic_condition", "get_route_with_traffic", "analyze_route_traffic"]
    COMPOSITE_TOOLS = ["get_via_route", "check_traffic_between_addresses", "get_detailed_route"]
    DESTINATION_TOOLS = ["save_destination", "list_destinations", "delete_destination", "update_destination"]


class MCPTypeConstants:
    """MCP Type constants for Literal types - use constants from Domain layer."""
    # Import constants from Domain layer to avoid duplicate
    from app.domain.constants.api_constants import TravelModeConstants
    
    # Travel mode values for Literal type - use constants from Domain
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
    """MCP Tool descriptions - Instructions for LLM to understand tool functionality."""
    
    # ROUTING TOOLS
    CALCULATE_ROUTE = """
    Calculate a route between two coordinates using TomTom Routing API.
    
    INPUT:
    - origin_lat: float (latitude of starting point)
    - origin_lon: float (longitude of starting point) 
    - dest_lat: float (latitude of destination)
    - dest_lon: float (longitude of destination)
    - travel_mode: str (optional, default: "car") - "car", "bicycle", or "foot"
    
    OUTPUT:
    - JSON with route summary (distance, duration) and route sections
    - Returns error if coordinates are invalid or route cannot be calculated
    """
    
    GET_DETAILED_ROUTE = """
    Calculate detailed route with step-by-step driving instructions between two addresses.
    
    INPUT:
    - origin_address: str (starting address)
    - destination_address: str (destination address)
    - travel_mode: str (optional, default: "car") - "car", "bicycle", or "foot"
    - country_set: str (optional, default: "VN")
    - language: str (optional, default: "vi-VN")
    
    OUTPUT:
    - JSON with detailed route including driving instructions, distances, times, and traffic info
    - Returns error if addresses cannot be found or route cannot be calculated
    """
    
    # GEOCODING TOOLS
    GEOCODE_ADDRESS = """
    Convert address to coordinates using TomTom Geocoding API.
    
    INPUT:
    - address: str (address to geocode)
    - country_set: str (optional, default: "VN")
    - limit: int (optional, default: 1) - max number of results
    - language: str (optional, default: "vi-VN")
    
    OUTPUT:
    - JSON with geocoding results including coordinates, formatted address, and confidence score
    - Returns error if address cannot be found
    """
    
    GET_INTERSECTION_POSITION = """
    Find coordinates of a specific intersection.
    
    INPUT:
    - street1: str (first street name)
    - street2: str (second street name)
    - country_set: str (optional, default: "VN")
    - language: str (optional, default: "vi-VN")
    
    OUTPUT:
    - JSON with intersection coordinates and formatted address
    - Returns error if intersection cannot be found
    """
    
    GET_STREET_CENTER_POSITION = """
    Find center coordinates of a specific street.
    
    INPUT:
    - street_name: str (name of the street)
    - country_set: str (optional, default: "VN")
    - language: str (optional, default: "vi-VN")
    
    OUTPUT:
    - JSON with street center coordinates and formatted address
    - Returns error if street cannot be found
    """
    
    # TRAFFIC TOOLS
    GET_TRAFFIC_CONDITION = """
    Get traffic condition information at a specific location.
    
    INPUT:
    - lat: float (latitude)
    - lon: float (longitude)
    - language: str (optional, default: "vi-VN")
    
    OUTPUT:
    - JSON with traffic condition data including flow, incidents, and delays
    - Returns error if location is invalid or traffic data unavailable
    """
    
    GET_ROUTE_WITH_TRAFFIC = """
    Calculate route with traffic information included.
    
    INPUT:
    - origin_lat: float (starting latitude)
    - origin_lon: float (starting longitude)
    - dest_lat: float (destination latitude)
    - dest_lon: float (destination longitude)
    - travel_mode: str (optional, default: "car")
    
    OUTPUT:
    - JSON with route summary and traffic-affected sections
    - Returns error if route cannot be calculated
    """
    
    GET_VIA_ROUTE = """
    Calculate route through intermediate waypoints (A → B → C).
    
    INPUT:
    - origin_lat: float (starting latitude)
    - origin_lon: float (starting longitude)
    - dest_lat: float (destination latitude)
    - dest_lon: float (destination longitude)
    - via_lat: float (intermediate waypoint latitude)
    - via_lon: float (intermediate waypoint longitude)
    - travel_mode: str (optional, default: "car")
    
    OUTPUT:
    - JSON with route summary passing through the intermediate waypoint
    - Returns error if coordinates are invalid or route cannot be calculated
    """
    
    ANALYZE_ROUTE_TRAFFIC = """
    Analyze traffic conditions on a route between two coordinates.
    
    INPUT:
    - origin_lat: float (starting latitude)
    - origin_lon: float (starting longitude)
    - dest_lat: float (destination latitude)
    - dest_lon: float (destination longitude)
    - travel_mode: str (optional, default: "car")
    
    OUTPUT:
    - JSON with traffic analysis including delays, incidents, and alternative routes
    - Returns error if coordinates are invalid or analysis cannot be performed
    """
    
    CHECK_TRAFFIC_BETWEEN_ADDRESSES = """
    Check traffic conditions between two addresses (automatically geocodes addresses).
    
    INPUT:
    - origin_address: str (starting address)
    - destination_address: str (destination address)
    - country_set: str (optional, default: "VN")
    - travel_mode: str (optional, default: "car")
    - language: str (optional, default: "vi-VN")
    
    OUTPUT:
    - JSON with traffic analysis between the two addresses
    - Returns error if addresses cannot be found or traffic data unavailable
    """
    
    # DESTINATION MANAGEMENT TOOLS
    SAVE_DESTINATION = """
    Save a destination for future use (automatically geocodes and stores coordinates).
    
    INPUT:
    - name: str (destination name)
    - address: str (destination address)
    
    OUTPUT:
    - JSON with success status, destination ID, and verification that data was saved to database
    - Returns error if address cannot be geocoded or destination already exists
    """
    
    LIST_DESTINATIONS = """
    List all saved destinations.
    
    INPUT:
    - None (no parameters required)
    
    OUTPUT:
    - JSON with list of all saved destinations including ID, name, address, coordinates, and timestamps
    - Returns empty list if no destinations are saved
    """
    
    DELETE_DESTINATION = """
    Delete a destination by name or address.
    
    INPUT:
    - name: str (optional) - destination name to delete
    - address: str (optional) - destination address to delete
    - Note: At least one of name or address must be provided
    
    OUTPUT:
    - JSON with success status and verification that destination was deleted from database
    - Returns error if no matching destination found or deletion failed
    """
    
    UPDATE_DESTINATION = """
    Update a destination's name or address.
    
    INPUT:
    - destination_id: str (ID of destination to update)
    - name: str (optional) - new name for destination
    - address: str (optional) - new address for destination
    - Note: At least one of name or address must be provided
    
    OUTPUT:
    - JSON with success status, destination ID, and verification that data was updated in database
    - Returns error if destination not found or update failed
    """


class MCPErrorMessages:
    """MCP Error messages."""
    # Server errors
    SERVER_STARTUP_ERROR = "[ERROR] Error starting server: {error}"
    CONFIG_ERROR = "[ERROR] Configuration error: {error}"
    API_KEY_MISSING = "[ERROR] TOMTOM_API_KEY environment variable is required!"
    
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
    API_KEY_CONFIGURED = "[SUCCESS] TomTom API key configured"
    TOOL_EXECUTED = "[SUCCESS] Tool executed successfully: {tool_name}"
    
    # Destination management success messages
    DESTINATION_UPDATED_SUCCESS = "Destination updated successfully"
    DESTINATION_SAVED_SUCCESS = "Destination saved successfully"
    DESTINATION_DELETED_SUCCESS = "Destination deleted successfully"
    DESTINATION_LISTED_SUCCESS = "Destination list retrieved successfully"
    
    # Destination management warning/error messages
    DESTINATION_UPDATE_DETAILS_NOT_FOUND = "Cannot get details of updated destination"
    DESTINATION_UPDATE_FAILED = "Destination update failed"
    DESTINATION_DELETE_VERIFICATION_FAILED = "Cannot verify destination deletion"
    DESTINATION_DELETE_FAILED = "Destination deletion failed"
    DESTINATION_DELETE_VERIFIED = "Verified: Destination has been removed from storage"
    DESTINATION_STILL_EXISTS = "Destination still exists in storage after deletion"
    DESTINATION_SEARCH_CRITERIA_MISSING = "Please provide name or address to search for destination to delete"
    DESTINATION_NOT_FOUND = "No destination found matching search criteria"
    DESTINATION_MULTIPLE_FOUND = "Found {count} matching destinations. Please provide more specific information"
    DESTINATION_BULK_DELETE_SUCCESS = "Successfully deleted {count} destinations"
    DESTINATION_PARTIAL_DELETE_SUCCESS = "Deleted {deleted_count} destinations, {failed_count} destinations failed"
    
    # Route calculation success messages
    ROUTE_CALCULATED_SUCCESS = "Route calculated successfully"
    ROUTE_WITH_TRAFFIC_SUCCESS = "Route with traffic information calculated successfully"
    DETAILED_ROUTE_SUCCESS = "Detailed route calculated successfully"
    
    # Geocoding success messages
    ADDRESS_GEOCODED_SUCCESS = "Address converted to coordinates successfully"
    INTERSECTION_FOUND_SUCCESS = "Intersection found successfully"
    STREET_CENTER_FOUND_SUCCESS = "Street center found successfully"
    
    # Traffic analysis success messages
    TRAFFIC_CONDITION_SUCCESS = "Traffic condition information retrieved successfully"
    TRAFFIC_ANALYSIS_SUCCESS = "Traffic analysis completed successfully"
    ADDRESS_TRAFFIC_CHECK_SUCCESS = "Traffic condition between addresses checked successfully"


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
   • calculate_route - Calculate basic route
   • geocode_address - Convert address to coordinates
   • get_intersection_position - Find intersection coordinates
   • get_street_center_position - Find street center position
   • get_traffic_condition - Get traffic information
   • get_route_with_traffic - Route with traffic
   • get_via_route - Route via intermediate points
   • analyze_route_traffic - Analyze route traffic
   • check_traffic_between_addresses - Check traffic between addresses"""
    
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
    ERROR_HEADER = "\n[ERROR] Error in get_detailed_route: {error}"


class MCPDestinationErrorMessages:
    """MCP Error messages for destination management."""
    # Destination management error messages
    MISSING_SEARCH_CRITERIA = "Missing search criteria"
    NO_MATCHING_DESTINATIONS = "No matching destinations found"
    UNKNOWN_ERROR = "Unknown error"
    PARTIAL_DELETION_SUCCESS = "Partial deletion success"
    ALL_DELETIONS_FAILED = "All deletions failed"

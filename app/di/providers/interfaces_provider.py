"""Interfaces layer dependencies provider."""

from typing import Dict, Any
from app.interfaces.constants.mcp_constants import MCPServerConstants


class InterfacesProvider:
    """Provider for interfaces layer dependencies."""
    
    def __init__(self, application_provider: Any):
        """Initialize interfaces provider with application dependencies."""
        self._application_provider = application_provider
    
    def get_mcp_server_config(self) -> Dict[str, Any]:
        """Get MCP server configuration."""
        return {
            "server_name": MCPServerConstants.SERVER_NAME,
            "default_transport": MCPServerConstants.DEFAULT_TRANSPORT,
            "server_host": MCPServerConstants.SERVER_HOST,
            "server_port": MCPServerConstants.SERVER_PORT
        }
    
    def get_mcp_tools(self) -> Dict[str, Any]:
        """Get MCP tools configuration."""
        return {
            "calculate_route": {
                "name": "calculate_route",
                "description": "Calculate a route between two points"
            },
            "geocode_address": {
                "name": "geocode_address", 
                "description": "Convert address to coordinates"
            },
            "save_destination": {
                "name": "save_destination",
                "description": "Save destination with automatic geocoding"
            },
            "get_route_with_traffic": {
                "name": "get_route_with_traffic",
                "description": "Get route with traffic information"
            },
            "get_intersection_position": {
                "name": "get_intersection_position",
                "description": "Get intersection position"
            },
            "get_street_center_position": {
                "name": "get_street_center_position",
                "description": "Get street center position"
            },
            "get_traffic_condition": {
                "name": "get_traffic_condition",
                "description": "Get traffic condition"
            },
            "get_via_route": {
                "name": "get_via_route",
                "description": "Get route via waypoints"
            },
            "analyze_route_traffic": {
                "name": "analyze_route_traffic",
                "description": "Analyze route traffic"
            },
            "check_traffic_between_addresses": {
                "name": "check_traffic_between_addresses",
                "description": "Check traffic between addresses"
            },
            "get_detailed_route": {
                "name": "get_detailed_route",
                "description": "Get detailed route between two addresses using saved destinations if available"
            },
            "list_destinations": {
                "name": "list_destinations",
                "description": "List all saved destinations"
            },
            "delete_destination": {
                "name": "delete_destination",
                "description": "Delete destination by ID"
            },
            "update_destination": {
                "name": "update_destination",
                "description": "Update destination information"
            }
        }
    
    def get_interface_services(self) -> Dict[str, Any]:
        """Get interface services."""
        return {
            "mcp_server_config": self.get_mcp_server_config(),
            "mcp_tools": self.get_mcp_tools()
        }

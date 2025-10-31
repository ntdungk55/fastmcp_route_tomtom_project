#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TomTom MCP Server với Clean Architecture.

Server này đã được refactor để tuân thủ Clean Architecture:
- Sử dụng Use Cases thay vì gọi trực tiếp API
- Dependency Injection thông qua Container
- Ports & Adapters pattern
- ACL để tránh vendor lock-in
"""

import os
import sys
import uuid
from dataclasses import asdict
from pathlib import Path
from typing import Literal

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Domain imports (removed unused imports)

# Application DTOs
from app.application.dto.detailed_route_dto import DetailedRouteRequest
from app.application.dto.save_destination_dto import SaveDestinationRequest
from app.application.dto.search_destinations_dto import SearchDestinationsRequest
from app.application.dto.delete_destination_dto import DeleteDestinationRequest
from app.application.dto.update_destination_dto import UpdateDestinationRequest
from app.application.dto.weather_dto import WeatherCheckRequest

# DI Container
from app.di.container import Container
from fastmcp import FastMCP

# Constants
from app.domain.constants.api_constants import TravelModeConstants, CountryConstants, LanguageConstants
from app.interfaces.constants.mcp_constants import MCPServerConstants, MCPToolDescriptions, MCPErrorMessages, MCPSuccessMessages, MCPToolNames, MCPToolErrorMessages

# FastMCP instance
mcp = FastMCP(MCPServerConstants.SERVER_NAME)

# Create Literal type from constants - using string literals from constants
# Note: "motorcycle" is accepted but will be treated as "car" by TomTom API
TravelModeLiteral = Literal["car", "bicycle", "foot", "motorcycle"]

# Container instance với Dependency Injection
_container = Container()

# FastMCP tool definitions

@mcp.tool(name=MCPToolNames.SAVE_DESTINATION)
async def save_destination_tool(
    name: str,
    address: str
) -> dict:
    f"""{MCPToolDescriptions.SAVE_DESTINATION}"""
    try:
        # Sử dụng Save Destination Use Case
        request = SaveDestinationRequest(
            name=name,
            address=address
        )
        
        result = await _container.save_destination.execute(request)
        
        # Log verification status
        if result.success:
            print(f"\n[SUCCESS] Save Destination Success: {result.message}")
            print(f"[ID] Destination ID: {result.destination_id}")
        else:
            print(f"\n[ERROR] Save Destination Failed: {result.error}")
        
        # Trả về response dưới dạng dict
        return asdict(result)
    except Exception as e:
        return {"error": MCPToolErrorMessages.SAVE_DESTINATION_FAILED.format(error=str(e))}

@mcp.tool(name=MCPToolNames.LIST_DESTINATIONS)
async def list_destinations_tool() -> dict:
    f"""{MCPToolDescriptions.LIST_DESTINATIONS}"""
    try:
        # Sử dụng Search Destinations Use Case với default values (list all)
        request = SearchDestinationsRequest()
        
        result = await _container.search_destinations.execute(request)
        
        # Trả về response dưới dạng dict
        return asdict(result)
    except Exception as e:
        return {"error": MCPToolErrorMessages.LIST_DESTINATIONS_FAILED.format(error=str(e))}

@mcp.tool(name=MCPToolNames.DELETE_DESTINATION)
async def delete_destination_tool(
    name: str | None = None,
    address: str | None = None
) -> dict:
    f"""{MCPToolDescriptions.DELETE_DESTINATION}"""
    try:
        # Kiểm tra có ít nhất một tiêu chí tìm kiếm
        if not name and not address:
            return {
                "success": False,
                "message": "Please provide either name or address to delete destination",
                "error": "Missing search criteria"
            }
        
        # Sử dụng SearchDestinationsUseCase để tìm kiếm
        search_request = SearchDestinationsRequest(name=name, address=address)
        search_result = await _container.search_destinations.execute(search_request)
        
        if not search_result.success or not search_result.destinations:
            return {
                "success": False,
                "message": "No destinations found matching the criteria",
                "error": "Destination not found"
            }
        
        # Lấy destination đầu tiên để xóa
        target_destination = search_result.destinations[0]
        
        # Sử dụng Delete Destination Use Case
        delete_request = DeleteDestinationRequest(destination_id=target_destination.id)
        result = await _container.delete_destination.execute(delete_request)
        
        # Log verification status
        if result.success:
            print(f"\n[SUCCESS] Delete Destination Success: {result.message}")
            print(f"📊 Deleted: {target_destination.name} at {target_destination.address}")
        else:
            print(f"\n[ERROR] Delete Destination Failed: {result.error}")
        
        # Trả về response dưới dạng dict
        return asdict(result)
    except Exception as e:
        return {"error": MCPToolErrorMessages.DELETE_DESTINATION_FAILED.format(error=str(e))}

@mcp.tool(name=MCPToolNames.UPDATE_DESTINATION)
async def update_destination_tool(
    destination_id: str,
    name: str | None = None,
    address: str | None = None
) -> dict:
    f"""{MCPToolDescriptions.UPDATE_DESTINATION}"""
    try:
        # Sử dụng Update Destination Use Case
        request = UpdateDestinationRequest(
            destination_id=destination_id,
            name=name,
            address=address
        )
        
        result = await _container.update_destination.execute(request)
        
        # Log verification status
        if result.success:
            print(f"\n[SUCCESS] Update Destination Success: {result.message}")
            print(f"[ID] Destination ID: {result.destination_id}")
        else:
            print(f"\n[ERROR] Update Destination Failed: {result.error}")
        
        # Trả về response dưới dạng dict
        return asdict(result)
    except Exception as e:
        return {"error": MCPToolErrorMessages.UPDATE_DESTINATION_FAILED.format(error=str(e))}

@mcp.tool(name=MCPToolNames.GET_DETAILED_ROUTE)
async def get_detailed_route_tool(
    origin_address: str,
    destination_address: str,
    travel_mode: TravelModeLiteral = TravelModeConstants.CAR,
    country_set: str = CountryConstants.DEFAULT,
    language: str = LanguageConstants.DEFAULT
) -> dict:
    f"""{MCPToolDescriptions.GET_DETAILED_ROUTE}"""
    try:
        # Sử dụng Get Detailed Route Use Case
        request = DetailedRouteRequest(
            origin_address=origin_address,
            destination_address=destination_address,
            travel_mode=travel_mode,
            country_set=country_set,
            language=language
        )
        
        result = await _container.get_detailed_route.execute(request)
        
        # Log the result with traffic information
        print(f"\n[ROUTE] Detailed Route: {origin_address} -> {destination_address}")
        print(f"[TRAVEL] Travel Mode: {result.travel_mode}")
        print(f"[DISTANCE] Distance: {result.main_route.total_distance_meters}m")
        print(f"[DURATION] Duration: {result.main_route.total_duration_seconds}s")
        print(f"[TRAFFIC] Traffic: {result.main_route.traffic_condition.description if result.main_route.traffic_condition else 'N/A'}")
        
        # Show traffic sections if available
        if hasattr(result.main_route, 'sections') and result.main_route.sections:
            print(f"[TRAFFIC SECTIONS] Found {len(result.main_route.sections)} traffic sections:")
            for i, section in enumerate(result.main_route.sections[:3]):  # Show first 3 sections
                # sections is a list of RouteSection objects
                print(f"   Section {i+1}: {section.start_address} -> {section.end_address}")
                print(f"     Delay: {section.delay_seconds}s, Magnitude: {section.magnitude}, Category: {section.simple_category}")
        
        if result.main_route.instructions:
            print(f"[INSTRUCTIONS] Instructions ({len(result.main_route.instructions)} steps):")
            for instr in result.main_route.instructions[:3]:  # Show first 3 steps
                print(f"   Step {instr.step}: {instr.instruction} ({instr.distance_meters}m, {instr.duration_seconds}s)")
        
        if result.alternative_routes:
            print(f"[ALTERNATIVES] Alternative Routes: {len(result.alternative_routes)}")
        
        # Trả về response dưới dạng dict
        return asdict(result)
    except Exception as e:
        print(f"\n❌ Error in get_detailed_route: {str(e)}")
        return {"error": MCPToolErrorMessages.GET_DETAILED_ROUTE_FAILED.format(error=str(e))}

@mcp.tool(name=MCPToolNames.CHECK_WEATHER)
async def check_weather_tool(
    location: str,
    units: str = "metric",
    language: str = "vi"
) -> dict:
    f"""{MCPToolDescriptions.CHECK_WEATHER}"""
    try:
        # Kiểm tra weather feature có được enable không
        if _container.get_weather is None:
            return {
                "success": False,
                "error": "Weather feature is not available. Please configure WEATHERAPI_API_KEY environment variable."
            }
        
        # Sử dụng Get Weather Use Case
        request = WeatherCheckRequest(
            location=location,
            units=units,
            language=language
        )
        
        result = await _container.get_weather.execute(request)
        
        # Log verification status
        if result.success:
            print(f"\n[SUCCESS] Weather Check Success")
            print(f"[LOCATION] {result.location} ({result.coordinates})")
            if result.weather_data:
                print(f"[WEATHER] {result.weather_data.description}")
                # Display temperature with appropriate unit symbol
                unit_symbol = "°C" if result.weather_data.units == "metric" else "°F" if result.weather_data.units == "imperial" else "K"
                print(f"[TEMPERATURE] {result.weather_data.temperature}{unit_symbol} (feels like {result.weather_data.feels_like}{unit_symbol})")
                print(f"[HUMIDITY] {result.weather_data.humidity}%")
                print(f"[PRESSURE] {result.weather_data.pressure} hPa")
                print(f"[WIND] {result.weather_data.wind_speed} m/s")
                if result.weather_data.visibility:
                    print(f"[VISIBILITY] {result.weather_data.visibility} m")
        else:
            print(f"\n[ERROR] Weather Check Failed: {result.error_message}")
        
        # Trả về response dưới dạng dict
        return asdict(result)
    except Exception as e:
        return {"error": MCPToolErrorMessages.CHECK_WEATHER_FAILED.format(error=str(e))}

# Traffic recommendations đã được chuyển vào TrafficMapper trong ACL layer
        
def main():
    """Start the TomTom MCP server với Clean Architecture."""
    print("Starting TomTom Route MCP Server (Clean Architecture)...")

    try:
        # Lấy configuration từ config service
        config = _container.config_service.get_config()
        
        print(MCPSuccessMessages.API_KEY_CONFIGURED)
        print("Architecture: Clean Architecture với Use Cases & Ports/Adapters")
        print("Dependency Injection: Container pattern")
        
        # Available tools (only essential ones)
        available_tools = [
            "get_detailed_route",
            "save_destination", 
            "list_destinations",
            "delete_destination",
            "update_destination"
        ]
        
        # Add weather tool if enabled
        if _container.get_weather is not None:
            available_tools.append("check_weather")
        
        print(f"Available tools ({len(available_tools)}):")
        print(f"   • get_detailed_route - {MCPToolDescriptions.GET_DETAILED_ROUTE}")
        print(f"   • save_destination - {MCPToolDescriptions.SAVE_DESTINATION}")
        print(f"   • list_destinations - {MCPToolDescriptions.LIST_DESTINATIONS}")
        print(f"   • delete_destination - {MCPToolDescriptions.DELETE_DESTINATION}")
        print(f"   • update_destination - {MCPToolDescriptions.UPDATE_DESTINATION}")
        if _container.get_weather is not None:
            print(f"   • check_weather - {MCPToolDescriptions.CHECK_WEATHER}")
        print("=" * 60)
        print(f"Transport: {MCPServerConstants.DEFAULT_TRANSPORT}")
        print(f"Endpoint: http://{config.server_host}:{config.server_port}")
        print("=" * 60)

        # Run the FastMCP server with HTTP Streamable transport
        mcp.run(transport=MCPServerConstants.DEFAULT_TRANSPORT, port=config.server_port, host=config.server_host)
    except ValueError as e:
        print(MCPErrorMessages.CONFIG_ERROR.format(error=e))
        print("Please set your TomTom API key:")
        print("  Windows: $env:TOMTOM_API_KEY='your_api_key_here'")
        print("  Linux/Mac: export TOMTOM_API_KEY='your_api_key_here'")
        sys.exit(1)
    except KeyboardInterrupt:
        print(f"\n{MCPSuccessMessages.SERVER_STOPPED}")
    except Exception as e:
        print(MCPErrorMessages.SERVER_STARTUP_ERROR.format(error=e))
        sys.exit(1)

if __name__ == "__main__":
    main()

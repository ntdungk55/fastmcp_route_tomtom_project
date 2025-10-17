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
from typing import Literal, Union

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Domain imports
from app.domain.enums.travel_mode import TravelMode
from app.domain.value_objects.latlon import LatLon

# Application DTOs
from app.application.dto.calculate_route_dto import CalculateRouteCommand
from app.application.dto.detailed_route_dto import DetailedRouteRequest
from app.application.dto.geocoding_dto import (
    GeocodeAddressCommandDTO,
    StructuredGeocodeCommandDTO,
)
from app.application.dto.save_destination_dto import SaveDestinationRequest
from app.application.dto.search_destinations_dto import SearchDestinationsRequest
from app.application.dto.delete_destination_dto import DeleteDestinationRequest
from app.application.dto.update_destination_dto import UpdateDestinationRequest
from app.application.dto.traffic_dto import (
    AddressTrafficCommandDTO,
    RouteWithTrafficCommandDTO,
    TrafficAnalysisCommandDTO,
    TrafficConditionCommandDTO,
    ViaRouteCommandDTO,
)

# DI Container
from app.di.container import Container
from app.application.use_cases.save_destination import SaveDestinationUseCase
from fastmcp import FastMCP

# Constants
from app.domain.constants.api_constants import LanguageConstants, CountryConstants, LimitConstants, TravelModeConstants
from app.application.constants.validation_constants import DefaultValues
from app.interfaces.constants.mcp_constants import MCPServerConstants, MCPToolDescriptions, MCPErrorMessages, MCPSuccessMessages, MCPTypeConstants, MCPToolNames, MCPToolErrorMessages, MCPDestinationErrorMessages

# FastMCP instance
mcp = FastMCP(MCPServerConstants.SERVER_NAME)

# Create Literal type from constants - using string literals from constants
TravelModeLiteral = Literal["car", "bicycle", "foot"]

# Container instance với Dependency Injection
_container = Container()

# FastMCP tool definitions
@mcp.tool(name=MCPToolNames.GEOCODE_ADDRESS)
async def geocode_address_tool(
    address: str,
    country_set: str = CountryConstants.DEFAULT,
    limit: int = LimitConstants.DEFAULT_GEOCODING_LIMIT,
    language: str = LanguageConstants.DEFAULT
) -> dict:
    f"""{MCPToolDescriptions.GEOCODE_ADDRESS}"""
    try:
        # Sử dụng Use Case thay vì gọi trực tiếp API
        cmd = GeocodeAddressCommandDTO(
            address=address,
            country_set=country_set,
            limit=limit,
            language=language
        )
        result = await _container.geocode_address.handle(cmd)
        
        # Chuyển đổi domain DTO thành dict cho MCP response
        return {
            "results": [{
                "position": {"lat": r.position.lat, "lon": r.position.lon},
                "address": asdict(r.address),
                "confidence": r.confidence
            } for r in result.results],
            "summary": result.summary
        }
    except Exception as e:
        return {"error": MCPToolErrorMessages.GEOCODING_FAILED.format(error=str(e))}

@mcp.tool(name=MCPToolNames.GET_ROUTE_WITH_TRAFFIC)
async def get_route_with_traffic_tool(
    origin_lat: Union[str, float],
    origin_lon: Union[str, float],
    dest_lat: Union[str, float],
    dest_lon: Union[str, float],
    travel_mode: str = DefaultValues.DEFAULT_TRAVEL_MODE,
    route_type: str = DefaultValues.DEFAULT_ROUTE_TYPE,
    max_alternatives: int = DefaultValues.DEFAULT_MAX_ALTERNATIVES,
    language: str = LanguageConstants.DEFAULT
) -> dict:
    f"""{MCPToolDescriptions.GET_ROUTE_WITH_TRAFFIC}"""
    try:
        # Sử dụng Route with Traffic Use Case
        validation_service = _container.validation_service
        cmd = RouteWithTrafficCommandDTO(
            origin=LatLon(validation_service.safe_float_convert(origin_lat), validation_service.safe_float_convert(origin_lon)),
            destination=LatLon(validation_service.safe_float_convert(dest_lat), validation_service.safe_float_convert(dest_lon)),
            travel_mode=travel_mode,
            route_type=route_type,
            max_alternatives=max_alternatives,
            language=language
        )
        
        result = await _container.traffic_adapter.get_route_with_traffic(cmd)
        
        return {
            "summary": asdict(result.summary),
            "sections": [asdict(s) for s in result.sections],
        }
    except Exception as e:
        return {"error": MCPToolErrorMessages.ROUTE_WITH_TRAFFIC_FAILED.format(error=str(e))}

@mcp.tool(name=MCPToolNames.GET_INTERSECTION_POSITION)
async def get_intersection_position_tool(
    street_name: str,
    cross_street: str,
    municipality: str,
    country_code: str = CountryConstants.DEFAULT,
    limit: int = 1,
    language: str = LanguageConstants.DEFAULT
) -> dict:
    f"""{MCPToolDescriptions.GET_INTERSECTION_POSITION}"""
    try:
        # Sử dụng Structured Geocoding Use Case
        cmd = StructuredGeocodeCommandDTO(
            street_name=street_name,
            cross_street=cross_street,
            municipality=municipality,
            country_code=country_code,
            limit=limit,
            language=language
        )
        result = await _container.get_intersection_position.handle(cmd)
        
        # Chuyển đổi domain response
        return {
            "results": [{
                "position": {"lat": r.position.lat, "lon": r.position.lon},
                "address": asdict(r.address),
                "confidence": r.confidence
            } for r in result.results],
            "summary": result.summary
        }
    except Exception as e:
        return {"error": MCPToolErrorMessages.INTERSECTION_LOOKUP_FAILED.format(error=str(e))}

@mcp.tool(name=MCPToolNames.GET_STREET_CENTER_POSITION)
async def get_street_center_position_tool(
    street_name: str,
    country_set: str = CountryConstants.DEFAULT,
    language: str = LanguageConstants.DEFAULT
) -> dict:
    f"""{MCPToolDescriptions.GET_STREET_CENTER_POSITION}"""
    try:
        # Sử dụng Street Center Use Case
        result = await _container.get_street_center.handle(
            street_name, country_set, language
        )
        
        # Chuyển đổi domain response
        return {
            "results": [{
                "position": {"lat": r.position.lat, "lon": r.position.lon},
                "address": asdict(r.address),
                "confidence": r.confidence
            } for r in result.results],
            "summary": result.summary
        }
    except Exception as e:
        return {"error": MCPToolErrorMessages.STREET_CENTER_LOOKUP_FAILED.format(error=str(e))}

@mcp.tool(name=MCPToolNames.GET_TRAFFIC_CONDITION)
async def get_traffic_condition_tool(
    latitude: Union[str, float],
    longitude: Union[str, float],
    zoom: int = LimitConstants.DEFAULT_TRAFFIC_ZOOM
) -> dict:
    f"""{MCPToolDescriptions.GET_TRAFFIC_CONDITION}"""
    try:
        # Chuyển đổi tọa độ và sử dụng Traffic Use Case
        validation_service = _container.validation_service
        location = LatLon(validation_service.safe_float_convert(latitude), validation_service.safe_float_convert(longitude))
        cmd = TrafficConditionCommandDTO(location=location, zoom=zoom)
        
        result = await _container.get_traffic_condition.handle(cmd)
        
        # Chuyển đổi domain response
        return {
            "location": {"lat": result.location.lat, "lon": result.location.lon},
            "flow_data": asdict(result.flow_data),
            "road_closure": result.road_closure
        }
    except Exception as e:
        return {"error": MCPToolErrorMessages.TRAFFIC_CONDITION_FAILED.format(error=str(e))}

@mcp.tool(name=MCPToolNames.GET_VIA_ROUTE)
async def get_via_route_tool(
    origin_lat: Union[str, float],
    origin_lon: Union[str, float],
    via_lat: Union[str, float],
    via_lon: Union[str, float],
    dest_lat: Union[str, float],
    dest_lon: Union[str, float],
    travel_mode: str = DefaultValues.DEFAULT_TRAVEL_MODE,
    language: str = LanguageConstants.DEFAULT
) -> dict:
    f"""{MCPToolDescriptions.GET_VIA_ROUTE}"""
    try:
        # Sử dụng Via Route Use Case
        validation_service = _container.validation_service
        cmd = ViaRouteCommandDTO(
            origin=LatLon(validation_service.safe_float_convert(origin_lat), validation_service.safe_float_convert(origin_lon)),
            via_point=LatLon(validation_service.safe_float_convert(via_lat), validation_service.safe_float_convert(via_lon)),
            destination=LatLon(validation_service.safe_float_convert(dest_lat), validation_service.safe_float_convert(dest_lon)),
            travel_mode=travel_mode,
            language=language
        )
        
        result = await _container.traffic_adapter.get_via_route(cmd)
        
        return {
            "summary": asdict(result.summary),
            "sections": [asdict(s) for s in result.sections],
        }
    except Exception as e:
        return {"error": MCPToolErrorMessages.VIA_ROUTE_FAILED.format(error=str(e))}

@mcp.tool(name=MCPToolNames.ANALYZE_ROUTE_TRAFFIC)
async def analyze_route_traffic_tool(
    origin_lat: Union[str, float],
    origin_lon: Union[str, float],
    dest_lat: Union[str, float],
    dest_lon: Union[str, float],
    language: str = LanguageConstants.DEFAULT
) -> dict:
    f"""{MCPToolDescriptions.ANALYZE_ROUTE_TRAFFIC}"""
    try:
        # Sử dụng Traffic Analysis Use Case
        validation_service = _container.validation_service
        cmd = TrafficAnalysisCommandDTO(
            origin=LatLon(validation_service.safe_float_convert(origin_lat), validation_service.safe_float_convert(origin_lon)),
            destination=LatLon(validation_service.safe_float_convert(dest_lat), validation_service.safe_float_convert(dest_lon)),
            language=language
        )
        
        result = await _container.analyze_route_traffic.handle(cmd)
        
        # Trả về domain DTO dưới dạng dict
        return asdict(result)
    except Exception as e:
        return {"error": MCPToolErrorMessages.TRAFFIC_ANALYSIS_FAILED.format(error=str(e))}

# Helper functions đã được thay thế bằng Use Cases trong Clean Architecture

@mcp.tool(name=MCPToolNames.CHECK_TRAFFIC_BETWEEN_ADDRESSES)
async def check_traffic_between_addresses_tool(
    origin_address: str,
    destination_address: str,
    country_set: str = CountryConstants.DEFAULT,
    travel_mode: str = TravelModeConstants.CAR,
    language: str = LanguageConstants.DEFAULT
) -> dict:
    f"""{MCPToolDescriptions.CHECK_TRAFFIC_BETWEEN_ADDRESSES}"""
    try:
        # Sử dụng Address Traffic Use Case - composite use case
        cmd = AddressTrafficCommandDTO(
            origin_address=origin_address,
            destination_address=destination_address,
            country_set=country_set,
            travel_mode=travel_mode,
            language=language
        )
        
        result = await _container.check_address_traffic.handle(cmd)
        
        # Trả về domain DTO dưới dạng dict
        return asdict(result)
    except Exception as e:
        return {"error": MCPToolErrorMessages.ADDRESS_TRAFFIC_CHECK_FAILED.format(error=str(e))}

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
        
        # Log the result
        print(f"\n[ROUTE] Detailed Route: {origin_address} -> {destination_address}")
        print(f"[TRAVEL] Travel Mode: {result.travel_mode}")
        print(f"[DISTANCE] Distance: {result.main_route.total_distance_meters}m")
        print(f"[DURATION] Duration: {result.main_route.total_duration_seconds}s")
        print(f"[TRAFFIC] Traffic: {result.main_route.traffic_condition.description if result.main_route.traffic_condition else 'N/A'}")
        
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
        
        # Tool count
        all_tools = (MCPServerConstants.ROUTING_TOOLS + 
                    MCPServerConstants.GEOCODING_TOOLS + 
                    MCPServerConstants.TRAFFIC_TOOLS + 
                    MCPServerConstants.COMPOSITE_TOOLS +
                    MCPServerConstants.DESTINATION_TOOLS)
        
        print(f"Available tools ({len(all_tools)}):")
        print(f"   • geocode_address - {MCPToolDescriptions.GEOCODE_ADDRESS}")
        print(f"   • get_intersection_position - {MCPToolDescriptions.GET_INTERSECTION_POSITION}")
        print(f"   • get_street_center_position - {MCPToolDescriptions.GET_STREET_CENTER_POSITION}")
        print(f"   • get_traffic_condition - {MCPToolDescriptions.GET_TRAFFIC_CONDITION}")
        print(f"   • get_route_with_traffic - {MCPToolDescriptions.GET_ROUTE_WITH_TRAFFIC}")
        print(f"   • get_via_route - {MCPToolDescriptions.GET_VIA_ROUTE}")
        print(f"   • analyze_route_traffic - {MCPToolDescriptions.ANALYZE_ROUTE_TRAFFIC}")
        print(f"   • check_traffic_between_addresses - {MCPToolDescriptions.CHECK_TRAFFIC_BETWEEN_ADDRESSES}")
        print(f"   • get_detailed_route - {MCPToolDescriptions.GET_DETAILED_ROUTE}")
        print(f"   • save_destination - {MCPToolDescriptions.SAVE_DESTINATION}")
        print(f"   • list_destinations - {MCPToolDescriptions.LIST_DESTINATIONS}")
        print(f"   • delete_destination - {MCPToolDescriptions.DELETE_DESTINATION}")
        print(f"   • update_destination - {MCPToolDescriptions.UPDATE_DESTINATION}")
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

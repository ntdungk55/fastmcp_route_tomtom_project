#!/usr/bin/env python3
"""TomTom MCP Server với Clean Architecture.

Server này đã được refactor để tuân thủ Clean Architecture:
- Sử dụng Use Cases thay vì gọi trực tiếp API
- Dependency Injection thông qua Container
- Ports & Adapters pattern
- ACL để tránh vendor lock-in
"""

import os
import sys
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
from app.application.dto.list_destinations_dto import ListDestinationsRequest
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
from app.interfaces.constants.mcp_constants import MCPServerConstants, MCPToolDescriptions, MCPErrorMessages, MCPSuccessMessages, MCPDetailedRouteLogMessages, MCPTypeConstants, MCPToolNames, MCPToolErrorMessages

# FastMCP instance
mcp = FastMCP(MCPServerConstants.SERVER_NAME)

# Create Literal type from constants - using string literals from constants
TravelModeLiteral = Literal["car", "bicycle", "foot"]

# Container instance với Dependency Injection
_container = Container()

# FastMCP tool definitions
@mcp.tool(name=MCPToolNames.CALCULATE_ROUTE)
async def calculate_route_tool(
    origin_lat: float,
    origin_lon: float,
    dest_lat: float,
    dest_lon: float,
    travel_mode: TravelModeLiteral = TravelModeConstants.CAR,
) -> dict:
    """Calculate a route (TomTom Routing API) and return a JSON summary."""
    try:
        validation_service = _container.validation_service
        origin_lat_float = validation_service.safe_float_convert(origin_lat)
        origin_lon_float = validation_service.safe_float_convert(origin_lon)
        dest_lat_float = validation_service.safe_float_convert(dest_lat)
        dest_lon_float = validation_service.safe_float_convert(dest_lon)
        
        cmd = CalculateRouteCommand(
            origin=LatLon(origin_lat_float, origin_lon_float),
            destination=LatLon(dest_lat_float, dest_lon_float),
            travel_mode=TravelMode(travel_mode),
        )
        plan = await _container.calculate_route.handle(cmd)
        result = {
            "summary": asdict(plan.summary),
            "sections": [asdict(s) for s in plan.sections],
        }
        
        # Log the result
        print(f"\n🔍 MCP Server Response for calculate_route:")
        print(f"📏 Distance: {plan.summary.distance_m:,} meters")
        print(f"⏱️ Duration: {plan.summary.duration_s:,} seconds")
        print(f"🚧 Sections: {len(plan.sections)}")
        
        return result
    except Exception as e:
        print(f"\n❌ Error in calculate_route: {str(e)}")
        return {"error": MCPToolErrorMessages.INVALID_COORDINATES.format(error=str(e))}

@mcp.tool(name=MCPToolNames.GEOCODE_ADDRESS)
async def geocode_address_tool(
    address: str,
    country_set: str = CountryConstants.DEFAULT,
    limit: int = LimitConstants.DEFAULT_GEOCODING_LIMIT,
    language: str = LanguageConstants.DEFAULT
) -> dict:
    """Chuyển đổi địa chỉ thành tọa độ (sử dụng Clean Architecture)."""
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
    """Tính toán tuyến đường có kèm thông tin giao thông (sử dụng Clean Architecture)."""
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
    """Tìm tọa độ giao lộ (sử dụng Clean Architecture)."""
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
    """Tìm tọa độ trung tâm đường phố (sử dụng Clean Architecture)."""
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
    """Lấy thông tin tình trạng giao thông (sử dụng Clean Architecture)."""
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
    """Tính toán tuyến đường qua điểm trung gian A → B → C (sử dụng Clean Architecture)."""
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
    """Phân tích tình trạng giao thông trên tuyến đường (sử dụng Clean Architecture)."""
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
    """Kiểm tra tình trạng giao thông giữa hai địa chỉ (sử dụng Clean Architecture)."""
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
    """Lưu điểm đến để sử dụng sau này (tự động tìm tọa độ bằng TomTom API)."""
    try:
        # Sử dụng Save Destination Use Case
        request = SaveDestinationRequest(
            name=name,
            address=address
        )
        
        result = await _container.save_destination.execute(request)
        
        # Trả về response dưới dạng dict
        return asdict(result)
    except Exception as e:
        return {"error": MCPToolErrorMessages.SAVE_DESTINATION_FAILED.format(error=str(e))}

@mcp.tool(name=MCPToolNames.LIST_DESTINATIONS)
async def list_destinations_tool() -> dict:
    """Liệt kê tất cả điểm đến đã lưu."""
    try:
        # Sử dụng List Destinations Use Case
        request = ListDestinationsRequest()
        
        result = await _container.list_destinations.execute(request)
        
        # Trả về response dưới dạng dict
        return asdict(result)
    except Exception as e:
        return {"error": MCPToolErrorMessages.LIST_DESTINATIONS_FAILED.format(error=str(e))}

@mcp.tool(name=MCPToolNames.DELETE_DESTINATION)
async def delete_destination_tool(
    destination_id: str
) -> dict:
    """Xóa điểm đến theo ID."""
    try:
        # Sử dụng Delete Destination Use Case
        request = DeleteDestinationRequest(destination_id=destination_id)
        
        result = await _container.delete_destination.execute(request)
        
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
    """Cập nhật điểm đến (tên hoặc địa chỉ)."""
    try:
        # Sử dụng Update Destination Use Case
        request = UpdateDestinationRequest(
            destination_id=destination_id,
            name=name,
            address=address
        )
        
        result = await _container.update_destination.execute(request)
        
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
    """Tính toán tuyến đường chi tiết và cung cấp chỉ dẫn từng bước di chuyển giữa hai địa chỉ, bao gồm hướng dẫn lái xe, khoảng cách, thời gian và thông tin giao thông."""
    try:
        # Sử dụng Get Detailed Route Use Case
        request = DetailedRouteRequest(
            origin_address=origin_address,
            destination_address=destination_address,
            travel_mode=TravelMode(travel_mode),
            country_set=country_set,
            language=language
        )
        
        result = await _container.get_detailed_route.handle(request)
        
        # Log the result for debugging
        print(MCPDetailedRouteLogMessages.SERVER_RESPONSE_HEADER)
        print(MCPDetailedRouteLogMessages.DISTANCE_LOG.format(distance=result.summary.distance_m))
        print(MCPDetailedRouteLogMessages.DURATION_LOG.format(duration=result.summary.duration_s))
        print(MCPDetailedRouteLogMessages.GUIDANCE_INSTRUCTIONS_LOG.format(count=len(result.guidance.instructions)))
        print(MCPDetailedRouteLogMessages.ROUTE_LEGS_LOG.format(count=len(result.legs)))
        print(MCPDetailedRouteLogMessages.ORIGIN_LOG.format(address=result.origin.address))
        print(MCPDetailedRouteLogMessages.DESTINATION_LOG.format(address=result.destination.address))
        
        # Show first few guidance instructions
        if result.guidance.instructions:
            print(MCPDetailedRouteLogMessages.GUIDANCE_HEADER)
            for i, inst in enumerate(result.guidance.instructions[:3]):
                print(MCPDetailedRouteLogMessages.GUIDANCE_STEP.format(step=i+1, instruction=inst.instruction))
                print(MCPDetailedRouteLogMessages.GUIDANCE_DISTANCE_DURATION.format(distance=inst.distance_m, duration=inst.duration_s))
                print(MCPDetailedRouteLogMessages.GUIDANCE_MANEUVER.format(maneuver=inst.maneuver))
                if inst.road_name:
                    print(MCPDetailedRouteLogMessages.GUIDANCE_ROAD.format(road_name=inst.road_name))
                print(MCPDetailedRouteLogMessages.GUIDANCE_POINT.format(lat=inst.point.lat, lon=inst.point.lon))
        
        # Convert to dict format - chỉ trả về guidance instructions (chỉ dẫn theo tuyến đường)
        response_dict = {
            "summary": {
                "distance_m": result.summary.distance_m,
                "duration_s": result.summary.duration_s,
                "traffic_delay_s": result.summary.traffic_delay_s,
                "fuel_consumption_l": result.summary.fuel_consumption_l
            },
            "route_instructions": [
                {
                    "step": i + 1,
                    "instruction": inst.instruction,
                    "distance_m": inst.distance_m,
                    "duration_s": inst.duration_s,
                    "maneuver": inst.maneuver,
                    "road_name": inst.road_name,
                    "point": {
                        "lat": inst.point.lat,
                        "lon": inst.point.lon,
                        "address": inst.point.address
                    }
                } for i, inst in enumerate(result.guidance.instructions)
            ],
            "waypoints": [
                {
                    "lat": wp.lat,
                    "lon": wp.lon,
                    "address": wp.address
                } for wp in result.waypoints
            ],
            "origin": {
                "lat": result.origin.lat,
                "lon": result.origin.lon,
                "address": result.origin.address
            },
            "destination": {
                "lat": result.destination.lat,
                "lon": result.destination.lon,
                "address": result.destination.address
            },
            "traffic_sections": result.traffic_sections,
            "route_legs": [
                {
                    "leg_number": i + 1,
                    "start_point": {
                        "lat": leg.start_point.lat,
                        "lon": leg.start_point.lon,
                        "address": leg.start_point.address
                    },
                    "end_point": {
                        "lat": leg.end_point.lat,
                        "lon": leg.end_point.lon,
                        "address": leg.end_point.address
                    },
                    "distance_m": leg.distance_m,
                    "duration_s": leg.duration_s
                } for i, leg in enumerate(result.legs)
            ],
            "route_geometry": [
                {
                    "lat": point.lat,
                    "lon": point.lon,
                    "address": point.address
                } for point in result.route_geometry
            ] if result.route_geometry else None
        }
        
        # Log the final response dict
        print(MCPDetailedRouteLogMessages.FINAL_RESPONSE_HEADER)
        print(MCPDetailedRouteLogMessages.SUMMARY_LOG.format(summary=response_dict['summary']))
        print(MCPDetailedRouteLogMessages.ROUTE_INSTRUCTIONS_COUNT.format(count=len(response_dict['route_instructions'])))
        print(MCPDetailedRouteLogMessages.ROUTE_LEGS_COUNT.format(count=len(response_dict['route_legs'])))
        print(MCPDetailedRouteLogMessages.TRAFFIC_SECTIONS_COUNT.format(count=len(response_dict['traffic_sections'])))
        
        # Show first few route instructions
        if response_dict['route_instructions']:
            print(MCPDetailedRouteLogMessages.ROUTE_INSTRUCTIONS_HEADER)
            for inst in response_dict['route_instructions'][:3]:
                print(MCPDetailedRouteLogMessages.ROUTE_STEP.format(step=inst['step'], instruction=inst['instruction']))
                print(MCPDetailedRouteLogMessages.ROUTE_DISTANCE_DURATION.format(distance=inst['distance_m'], duration=inst['duration_s']))
                print(MCPDetailedRouteLogMessages.ROUTE_MANEUVER.format(maneuver=inst['maneuver']))
                if inst['road_name']:
                    print(MCPDetailedRouteLogMessages.ROUTE_ROAD.format(road_name=inst['road_name']))
        
        return response_dict
    except Exception as e:
        print(MCPDetailedRouteLogMessages.ERROR_HEADER.format(error=str(e)))
        return {"error": MCPToolErrorMessages.GET_DETAILED_ROUTE_FAILED.format(error=str(e))}

# Traffic recommendations đã được chuyển vào TrafficMapper trong ACL layer
        
def main():
    """Start the TomTom MCP server với Clean Architecture."""
    print("🚀 Starting TomTom Route MCP Server (Clean Architecture)...")

    try:
        # Lấy configuration từ config service
        config = _container.config_service.get_config()
        
        print(MCPSuccessMessages.API_KEY_CONFIGURED)
        print("🏠 Architecture: Clean Architecture với Use Cases & Ports/Adapters")
        print("🔌 Dependency Injection: Container pattern")
        
        # Tool count
        all_tools = (MCPServerConstants.ROUTING_TOOLS + 
                    MCPServerConstants.GEOCODING_TOOLS + 
                    MCPServerConstants.TRAFFIC_TOOLS + 
                    MCPServerConstants.COMPOSITE_TOOLS +
                    MCPServerConstants.DESTINATION_TOOLS)
        
        print(f"🛠️  Available tools ({len(all_tools)}):")
        print(f"   • calculate_route - {MCPToolDescriptions.CALCULATE_ROUTE}")
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
        print(f"🌐 Transport: {MCPServerConstants.DEFAULT_TRANSPORT}")
        print(f"📡 Endpoint: http://{config.server_host}:{config.server_port}")
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

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
from app.domain.constants.api_constants import LanguageConstants, CountryConstants, LimitConstants
from app.application.constants.validation_constants import DefaultValues
from app.interfaces.constants.mcp_constants import MCPServerConstants, MCPToolDescriptions, MCPErrorMessages, MCPSuccessMessages

# FastMCP instance
mcp = FastMCP(MCPServerConstants.SERVER_NAME)

# Container instance với Dependency Injection
_container = Container()

# FastMCP tool definitions
@mcp.tool(name="calculate_route")
async def calculate_route_tool(
    origin_lat: float,
    origin_lon: float,
    dest_lat: float,
    dest_lon: float,
    travel_mode: Literal["car", "bicycle", "foot"] = "car",
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
        return {
            "summary": asdict(plan.summary),
            "sections": [asdict(s) for s in plan.sections],
        }
    except Exception as e:
        return {"error": f"Invalid coordinates: {str(e)}"}

@mcp.tool(name="geocode_address")
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
        return {"error": f"Geocoding failed: {str(e)}"}

@mcp.tool(name="get_route_with_traffic")
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
        return {"error": f"Route with traffic calculation failed: {str(e)}"}

@mcp.tool(name="get_intersection_position")
async def get_intersection_position_tool(
    street_name: str,
    cross_street: str,
    municipality: str,
    country_code: str = "VN",
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
        return {"error": f"Intersection lookup failed: {str(e)}"}

@mcp.tool(name="get_street_center_position")
async def get_street_center_position_tool(
    street_name: str,
    country_set: str = "VN",
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
        return {"error": f"Street center lookup failed: {str(e)}"}

@mcp.tool(name="get_traffic_condition")
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
        return {"error": f"Traffic condition lookup failed: {str(e)}"}

@mcp.tool(name="get_via_route")
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
        return {"error": f"Via route calculation failed: {str(e)}"}

@mcp.tool(name="analyze_route_traffic")
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
        return {"error": f"Traffic analysis failed: {str(e)}"}

# Helper functions đã được thay thế bằng Use Cases trong Clean Architecture

@mcp.tool(name="check_traffic_between_addresses")
async def check_traffic_between_addresses_tool(
    origin_address: str,
    destination_address: str,
    country_set: str = "VN",
    travel_mode: str = "car",
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
        return {"error": f"Address traffic check failed: {str(e)}"}

@mcp.tool(name="save_destination")
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
        return {"error": f"Save destination failed: {str(e)}"}

@mcp.tool(name="list_destinations")
async def list_destinations_tool() -> dict:
    """Liệt kê tất cả điểm đến đã lưu."""
    try:
        # Sử dụng List Destinations Use Case
        request = ListDestinationsRequest()
        
        result = await _container.list_destinations.execute(request)
        
        # Trả về response dưới dạng dict
        return asdict(result)
    except Exception as e:
        return {"error": f"List destinations failed: {str(e)}"}

@mcp.tool(name="delete_destination")
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
        return {"error": f"Delete destination failed: {str(e)}"}

@mcp.tool(name="update_destination")
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
        return {"error": f"Update destination failed: {str(e)}"}

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
                    MCPServerConstants.COMPOSITE_TOOLS)
        
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

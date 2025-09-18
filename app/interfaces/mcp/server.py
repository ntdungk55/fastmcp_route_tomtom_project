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
from app.application.dto.traffic_dto import (
    AddressTrafficCommandDTO,
    RouteWithTrafficCommandDTO,
    TrafficAnalysisCommandDTO,
    TrafficConditionCommandDTO,
    ViaRouteCommandDTO,
)

# DI Container
from app.di.container import Container
from fastmcp import FastMCP

# FastMCP instance
mcp = FastMCP("RouteMCP_TomTom_CleanArch")

# Container instance với Dependency Injection
_container = Container()

# Global API key - loaded once at startup
API_KEY = os.getenv("TOMTOM_API_KEY")

def safe_float_convert(value: Union[str, float, int]) -> float:
    """Convert string, int, or float to float safely."""
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value).strip())
    except (ValueError, TypeError) as e:
        raise ValueError(f"Cannot convert '{value}' to float: {e}")

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
        origin_lat_float = safe_float_convert(origin_lat)
        origin_lon_float = safe_float_convert(origin_lon)
        dest_lat_float = safe_float_convert(dest_lat)
        dest_lon_float = safe_float_convert(dest_lon)
        
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
    country_set: str = "VN",
    limit: int = 1,
    language: str = "vi-VN"
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
    travel_mode: str = "motorcycle",
    route_type: str = "fastest",
    max_alternatives: int = 1,
    language: str = "vi-VN"
) -> dict:
    """Tính toán tuyến đường có kèm thông tin giao thông (sử dụng Clean Architecture)."""
    try:
        # Sử dụng Route with Traffic Use Case
        cmd = RouteWithTrafficCommandDTO(
            origin=LatLon(safe_float_convert(origin_lat), safe_float_convert(origin_lon)),
            destination=LatLon(safe_float_convert(dest_lat), safe_float_convert(dest_lon)),
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
    language: str = "vi-VN"
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
    language: str = "vi-VN"
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
    zoom: int = 10
) -> dict:
    """Lấy thông tin tình trạng giao thông (sử dụng Clean Architecture)."""
    try:
        # Chuyển đổi tọa độ và sử dụng Traffic Use Case
        location = LatLon(safe_float_convert(latitude), safe_float_convert(longitude))
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
    travel_mode: str = "motorcycle",
    language: str = "vi-VN"
) -> dict:
    """Tính toán tuyến đường qua điểm trung gian A → B → C (sử dụng Clean Architecture)."""
    try:
        # Sử dụng Via Route Use Case
        cmd = ViaRouteCommandDTO(
            origin=LatLon(safe_float_convert(origin_lat), safe_float_convert(origin_lon)),
            via_point=LatLon(safe_float_convert(via_lat), safe_float_convert(via_lon)),
            destination=LatLon(safe_float_convert(dest_lat), safe_float_convert(dest_lon)),
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
    language: str = "vi-VN"
) -> dict:
    """Phân tích tình trạng giao thông trên tuyến đường (sử dụng Clean Architecture)."""
    try:
        # Sử dụng Traffic Analysis Use Case
        cmd = TrafficAnalysisCommandDTO(
            origin=LatLon(safe_float_convert(origin_lat), safe_float_convert(origin_lon)),
            destination=LatLon(safe_float_convert(dest_lat), safe_float_convert(dest_lon)),
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
    language: str = "vi-VN"
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

# Traffic recommendations đã được chuyển vào TrafficMapper trong ACL layer
        
def main():
    """Start the TomTom MCP server với Clean Architecture."""
    print("🚀 Starting TomTom Route MCP Server (Clean Architecture)...")

    # Check required environment variables
    if not API_KEY:
        print("❌ ERROR: TOMTOM_API_KEY environment variable is required!")
        print("Please set your TomTom API key:")
        print("  Windows: $env:TOMTOM_API_KEY='your_api_key_here'")
        print("  Linux/Mac: export TOMTOM_API_KEY='your_api_key_here'")
        sys.exit(1)

    print("✅ TomTom API key configured")
    print("🏠 Architecture: Clean Architecture với Use Cases & Ports/Adapters")
    print("🔌 Dependency Injection: Container pattern")
    print("🛠️  Available tools:")
    print("   • calculate_route - Tính toán tuyến đường cơ bản")
    print("   • geocode_address - Chuyển địa chỉ thành tọa độ")
    print("   • get_intersection_position - Tìm tọa độ giao lộ")
    print("   • get_street_center_position - Tìm trung tâm đường phố")
    print("   • get_traffic_condition - Lấy thông tin giao thông")
    print("   • get_route_with_traffic - Tuyến đường có traffic")
    print("   • get_via_route - Tuyến đường qua điểm trung gian")
    print("   • analyze_route_traffic - Phân tích traffic tuyến đường")
    print("   • check_traffic_between_addresses - Kiểm tra traffic giữa địa chỉ")
    print("=" * 60)
    print("🌐 Transport: HTTP Streamable")
    print("📡 Endpoint: http://192.168.1.3:8081")
    print("=" * 60)

    # Run the FastMCP server with HTTP Streamable transport
    try:
        mcp.run(transport="streamable-http", port=8081, host="192.168.1.3")
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""HTTP Streamable MCP Server for TomTom Route using FastMCP
Run TomTom Route MCP Server over HTTP Streamable using FastMCP
"""

import os
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Literal, Union

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

from app.application.dto.calculate_route_dto import CalculateRouteCommand
from app.di.container import Container
from app.domain.enums.travel_mode import TravelMode
from app.domain.value_objects.latlon import LatLon
from fastmcp import FastMCP

# FastMCP instance
mcp = FastMCP("RouteMCP_TomTom")

# Container instance
_container = Container()

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
    """Get latitude and longitude from an address using TomTom Geocoding API."""
    try:
        import httpx
        api_key = os.getenv("TOMTOM_API_KEY")
        if not api_key:
            return {"error": "TOMTOM_API_KEY not configured"}

        url = f"https://api.tomtom.com/search/2/geocode/{address}.json"
        params = {
            "key": api_key,
            "countrySet": country_set,
            "limit": limit,
            "language": language
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return {"error": str(e)}

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
    """Get the best route with traffic conditions using TomTom Routing API."""
    try:
        import httpx
        api_key = os.getenv("TOMTOM_API_KEY")
        if not api_key:
            return {"error": "TOMTOM_API_KEY not configured"}

        # Convert coordinates to float
        origin_lat_float = safe_float_convert(origin_lat)
        origin_lon_float = safe_float_convert(origin_lon)
        dest_lat_float = safe_float_convert(dest_lat)
        dest_lon_float = safe_float_convert(dest_lon)

        url = f"https://api.tomtom.com/routing/1/calculateRoute/{origin_lat_float},{origin_lon_float}:{dest_lat_float},{dest_lon_float}/json"
        params = {
            "key": api_key,
            "traffic": "true",
            "sectionType": "traffic",
            "instructionsType": "text",
            "language": language,
            "maxAlternatives": max_alternatives,
            "travelMode": travel_mode,
            "routeType": route_type
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return {"error": str(e)}

@mcp.tool(name="get_intersection_position")
async def get_intersection_position_tool(
    street_name: str,
    cross_street: str,
    municipality: str,
    country_code: str = "VN",
    limit: int = 1,
    language: str = "vi-VN"
) -> dict:
    """Get intersection position using TomTom Structured Geocoding API."""
    try:
        import httpx
        api_key = os.getenv("TOMTOM_API_KEY")
        if not api_key:
            return {"error": "TOMTOM_API_KEY not configured"}

        url = "https://api.tomtom.com/search/2/structuredGeocode.json"
        params = {
            "key": api_key,
            "countryCode": country_code,
            "streetName": street_name,
            "crossStreet": cross_street,
            "municipality": municipality,
            "limit": limit,
            "language": language
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return {"error": str(e)}

@mcp.tool(name="get_street_center_position")
async def get_street_center_position_tool(
    street_name: str,
    country_set: str = "VN",
    idx_set: str = "Str",
    limit: int = 1,
    language: str = "vi-VN"
) -> dict:
    """Get street's center point position using TomTom Search API."""
    try:
        import httpx
        api_key = os.getenv("TOMTOM_API_KEY")
        if not api_key:
            return {"error": "TOMTOM_API_KEY not configured"}

        url = f"https://api.tomtom.com/search/2/search/{street_name}.json"
        params = {
            "key": api_key,
            "countrySet": country_set,
            "idxSet": idx_set,
            "limit": limit,
            "language": language
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return {"error": str(e)}

@mcp.tool(name="get_traffic_condition")
async def get_traffic_condition_tool(
    latitude: Union[str, float],
    longitude: Union[str, float],
    zoom: int = 10
) -> dict:
    """Get traffic condition by center point using TomTom Traffic Flow API."""
    try:
        import httpx
        api_key = os.getenv("TOMTOM_API_KEY")
        if not api_key:
            return {"error": "TOMTOM_API_KEY not configured"}

        # Convert coordinates to float
        lat_float = safe_float_convert(latitude)
        lon_float = safe_float_convert(longitude)

        url = f"https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/{zoom}/json"
        params = {
            "key": api_key,
            "point": f"{lat_float},{lon_float}"
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return {"error": str(e)}

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
    """Travel from A to B via C using TomTom Routing API."""
    try:
        import httpx
        api_key = os.getenv("TOMTOM_API_KEY")
        if not api_key:
            return {"error": "TOMTOM_API_KEY not configured"}

        # Convert coordinates to float
        origin_lat_float = safe_float_convert(origin_lat)
        origin_lon_float = safe_float_convert(origin_lon)
        via_lat_float = safe_float_convert(via_lat)
        via_lon_float = safe_float_convert(via_lon)
        dest_lat_float = safe_float_convert(dest_lat)
        dest_lon_float = safe_float_convert(dest_lon)

        url = f"https://api.tomtom.com/routing/1/calculateRoute/{origin_lat_float},{origin_lon_float}:{via_lat_float},{via_lon_float}:{dest_lat_float},{dest_lon_float}/json"
        params = {
            "key": api_key,
            "traffic": "true",
            "sectionType": "traffic",
            "instructionsType": "text",
            "language": language
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return {"error": str(e)}

@mcp.tool(name="get_route_traffic_analysis")
async def get_route_traffic_analysis_tool(
    origin_lat: Union[str, float],
    origin_lon: Union[str, float],
    dest_lat: Union[str, float],
    dest_lon: Union[str, float],
    language: str = "vi-VN"
) -> dict:
    """Get best route A→B and check for heavy traffic sections using TomTom Routing API."""
    try:
        import httpx
        api_key = os.getenv("TOMTOM_API_KEY")
        if not api_key:
            return {"error": "TOMTOM_API_KEY not configured"}

        # Convert coordinates to float
        origin_lat_float = safe_float_convert(origin_lat)
        origin_lon_float = safe_float_convert(origin_lon)
        dest_lat_float = safe_float_convert(dest_lat)
        dest_lon_float = safe_float_convert(dest_lon)

        url = f"https://api.tomtom.com/routing/1/calculateRoute/{origin_lat_float},{origin_lon_float}:{dest_lat_float},{dest_lon_float}/json"
        params = {
            "key": api_key,
            "traffic": "true",
            "sectionType": "traffic",
            "instructionsType": "text",
            "language": language
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return {"error": str(e)}

async def _geocode_address_helper(address: str, country_set: str = "VN", limit: int = 1, language: str = "vi-VN") -> dict:
    """Helper function to geocode an address."""
    try:
        import httpx
        api_key = os.getenv("TOMTOM_API_KEY")
        if not api_key:
            return {"error": "TOMTOM_API_KEY not configured"}

        url = f"https://api.tomtom.com/search/2/geocode/{address}.json"
        params = {
            "key": api_key,
            "countrySet": country_set,
            "limit": limit,
            "language": language
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return {"error": str(e)}

async def _get_route_traffic_analysis_helper(
    origin_lat: Union[str, float],
    origin_lon: Union[str, float],
    dest_lat: Union[str, float],
    dest_lon: Union[str, float],
    language: str = "vi-VN"
) -> dict:
    """Helper function to get route traffic analysis."""
    try:
        import httpx
        api_key = os.getenv("TOMTOM_API_KEY")
        if not api_key:
            return {"error": "TOMTOM_API_KEY not configured"}

        # Convert coordinates to float
        origin_lat_float = safe_float_convert(origin_lat)
        origin_lon_float = safe_float_convert(origin_lon)
        dest_lat_float = safe_float_convert(dest_lat)
        dest_lon_float = safe_float_convert(dest_lon)

        url = f"https://api.tomtom.com/routing/1/calculateRoute/{origin_lat_float},{origin_lon_float}:{dest_lat_float},{dest_lon_float}/json"
        params = {
            "key": api_key,
            "traffic": "true",
            "sectionType": "traffic",
            "instructionsType": "text",
            "language": language
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return {"error": str(e)}

@mcp.tool(name="check_traffic_between_addresses")
async def check_traffic_between_addresses_tool(
    origin_address: str,
    destination_address: str,
    country_set: str = "VN",
    travel_mode: str = "car",
    language: str = "vi-VN"
) -> dict:
    """Check traffic conditions between two addresses by geocoding addresses and analyzing route traffic."""
    try:
        # Step 1: Geocode both addresses to get coordinates
        origin_geocode = await _geocode_address_helper(origin_address, country_set, 1, language)
        dest_geocode = await _geocode_address_helper(destination_address, country_set, 1, language)
        
        # Check for geocoding errors
        if "error" in origin_geocode:
            return {"error": f"Failed to geocode origin address: {origin_geocode['error']}"}
        if "error" in dest_geocode:
            return {"error": f"Failed to geocode destination address: {dest_geocode['error']}"}
        
        # Extract coordinates
        origin_results = origin_geocode.get("results", [])
        dest_results = dest_geocode.get("results", [])
        
        if not origin_results:
            return {"error": f"No results found for origin address: {origin_address}"}
        if not dest_results:
            return {"error": f"No results found for destination address: {destination_address}"}
        
        origin_coords = origin_results[0]["position"]
        dest_coords = dest_results[0]["position"]
        
        origin_lat = origin_coords["lat"]
        origin_lon = origin_coords["lon"]
        dest_lat = dest_coords["lat"]
        dest_lon = dest_coords["lon"]
        
        # Step 2: Get route with traffic analysis
        traffic_analysis = await _get_route_traffic_analysis_helper(
            origin_lat, origin_lon, dest_lat, dest_lon, language
        )
        
        if "error" in traffic_analysis:
            return {"error": f"Failed to get traffic analysis: {traffic_analysis['error']}"}
        
        # Step 3: Analyze traffic conditions
        routes = traffic_analysis.get("routes", [])
        if not routes:
            return {"error": "No routes found"}
        
        route = routes[0]
        summary = route.get("summary", {})
        sections = route.get("sections", [])
        
        # Count traffic conditions
        traffic_conditions = {
            "FLOWING": 0,
            "SLOW": 0, 
            "JAM": 0,
            "CLOSED": 0,
            "UNKNOWN": 0
        }
        
        heavy_traffic_sections = []
        for i, section in enumerate(sections):
            section_type = section.get("sectionType", "")
            simple_category = section.get("simpleCategory", "")
            
            if simple_category:
                traffic_conditions[simple_category] = traffic_conditions.get(simple_category, 0) + 1
                if simple_category in ["SLOW", "JAM", "CLOSED"]:
                    heavy_traffic_sections.append({
                        "section_index": i,
                        "condition": simple_category,
                        "start_index": section.get("startPointIndex", 0),
                        "end_index": section.get("endPointIndex", 0)
                    })
        
        # Calculate traffic severity score (0-100, higher = worse traffic)
        total_sections = len(sections)
        if total_sections > 0:
            traffic_score = (
                traffic_conditions["SLOW"] * 30 +
                traffic_conditions["JAM"] * 70 +
                traffic_conditions["CLOSED"] * 100
            ) / total_sections
        else:
            traffic_score = 0
        
        # Determine overall traffic status
        if traffic_score >= 70:
            overall_status = "HEAVY_TRAFFIC"
        elif traffic_score >= 30:
            overall_status = "MODERATE_TRAFFIC"
        else:
            overall_status = "LIGHT_TRAFFIC"
        
        return {
            "origin": {
                "address": origin_address,
                "coordinates": {"lat": origin_lat, "lon": origin_lon},
                "geocoded_address": origin_results[0].get("address", {}).get("freeformAddress", origin_address)
            },
            "destination": {
                "address": destination_address,
                "coordinates": {"lat": dest_lat, "lon": dest_lon},
                "geocoded_address": dest_results[0].get("address", {}).get("freeformAddress", destination_address)
            },
            "route_summary": {
                "distance_meters": summary.get("lengthInMeters", 0),
                "duration_seconds": summary.get("travelTimeInSeconds", 0),
                "duration_traffic_seconds": summary.get("trafficDelayInSeconds", 0)
            },
            "traffic_analysis": {
                "overall_status": overall_status,
                "traffic_score": round(traffic_score, 2),
                "conditions_count": traffic_conditions,
                "heavy_traffic_sections": heavy_traffic_sections,
                "total_sections": total_sections
            },
            "recommendations": _get_traffic_recommendations(overall_status, traffic_score, heavy_traffic_sections)
        }
        
    except Exception as e:
        return {"error": f"Error checking traffic between addresses: {str(e)}"}

def _get_traffic_recommendations(status: str, score: float, heavy_sections: list) -> list:
    """Generate traffic recommendations based on analysis."""
    recommendations = []
    
    if status == "HEAVY_TRAFFIC":
        recommendations.append("🚨 Tình trạng giao thông rất tệ - nên tránh tuyến đường này")
        recommendations.append("⏰ Nên đi sớm hơn hoặc muộn hơn để tránh giờ cao điểm")
        recommendations.append("🔄 Cân nhắc sử dụng phương tiện công cộng")
    elif status == "MODERATE_TRAFFIC":
        recommendations.append("⚠️ Tình trạng giao thông trung bình - có thể có kẹt xe nhẹ")
        recommendations.append("📱 Theo dõi tình hình giao thông trong quá trình di chuyển")
    else:
        recommendations.append("✅ Tình trạng giao thông tốt - có thể di chuyển bình thường")
    
    if heavy_sections:
        recommendations.append(f"🚧 Có {len(heavy_sections)} đoạn đường bị kẹt xe nặng")
    
    if score > 50:
        recommendations.append("🕐 Thời gian di chuyển có thể tăng 50% so với bình thường")
    
    return recommendations
        
def main():
    """Start the MCP server using FastMCP with HTTP Streamable transport."""
    print("🚀 Starting TomTom Route MCP Server with FastMCP (HTTP Streamable)...")

    # Check required environment variables
    if not os.getenv("TOMTOM_API_KEY"):
        print("❌ ERROR: TOMTOM_API_KEY environment variable is required!")
        print("Please set your TomTom API key:")
        print("  Windows: $env:TOMTOM_API_KEY='your_api_key_here'")
        print("  Linux/Mac: export TOMTOM_API_KEY='your_api_key_here'")
        sys.exit(1)

    print("✅ TomTom API key configured")
    print("🛠️  Available tools:")
    print("   • calculate_route - Calculate route with traffic conditions")
    print("   • geocode_address - Convert address to lat/lon coordinates")
    print("   • get_route_with_traffic - Get best route with traffic data")
    print("   • get_intersection_position - Find intersection coordinates")
    print("   • get_street_center_position - Get street center point")
    print("   • get_traffic_condition - Get traffic flow data by location")
    print("   • get_via_route - Calculate route A→B via C")
    print("   • get_route_traffic_analysis - Analyze route for heavy traffic")
    print("   • check_traffic_between_addresses - Check traffic between two addresses")
    print("   • test_map_tile - Test TomTom API key with map tiles")
    print("=" * 50)
    print("🌐 Server will run on HTTP Streamable transport")
    print("📡 Endpoint: http://192.168.1.3:8081")
    print("=" * 50)

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


import os
from dataclasses import asdict
from typing import Literal

from app.application.dto.calculate_route_dto import CalculateRouteCommand
from app.di.container import Container
from app.domain.enums.travel_mode import TravelMode
from app.domain.value_objects.latlon import LatLon
from fastmcp import FastMCP  # pip install fastmcp

mcp = FastMCP("RouteMCP_TomTom")
_container = Container()

@mcp.tool()
async def calculate_route(
    origin_lat: float,
    origin_lon: float,
    dest_lat: float,
    dest_lon: float,
    travel_mode: Literal["car", "bicycle", "foot"] = "car",
) -> dict:
    """Calculate a route (TomTom Routing API) and return a JSON summary."""
    cmd = CalculateRouteCommand(
        origin=LatLon(origin_lat, origin_lon),
        destination=LatLon(dest_lat, dest_lon),
        travel_mode=TravelMode(travel_mode),
    )
    plan = await _container.calculate_route.handle(cmd)
    return {
        "summary": asdict(plan.summary),
        "sections": [asdict(s) for s in plan.sections],
    }

@mcp.tool()
async def geocode_address(
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

@mcp.tool()
async def get_route_with_traffic(
    origin_lat: float,
    origin_lon: float,
    dest_lat: float,
    dest_lon: float,
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

        url = f"https://api.tomtom.com/routing/1/calculateRoute/{origin_lat},{origin_lon}:{dest_lat},{dest_lon}/json"
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

@mcp.tool()
async def get_intersection_position(
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

@mcp.tool()
async def get_street_center_position(
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

@mcp.tool()
async def get_traffic_condition(
    latitude: float,
    longitude: float,
    zoom: int = 10
) -> dict:
    """Get traffic condition by center point using TomTom Traffic Flow API."""
    try:
        import httpx
        api_key = os.getenv("TOMTOM_API_KEY")
        if not api_key:
            return {"error": "TOMTOM_API_KEY not configured"}

        url = f"https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/{zoom}/json"
        params = {
            "key": api_key,
            "point": f"{latitude},{longitude}"
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
async def get_via_route(
    origin_lat: float,
    origin_lon: float,
    via_lat: float,
    via_lon: float,
    dest_lat: float,
    dest_lon: float,
    travel_mode: str = "motorcycle",
    language: str = "vi-VN"
) -> dict:
    """Travel from A to B via C using TomTom Routing API."""
    try:
        import httpx
        api_key = os.getenv("TOMTOM_API_KEY")
        if not api_key:
            return {"error": "TOMTOM_API_KEY not configured"}

        url = f"https://api.tomtom.com/routing/1/calculateRoute/{origin_lat},{origin_lon}:{via_lat},{via_lon}:{dest_lat},{dest_lon}/json"
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

@mcp.tool()
async def get_route_traffic_analysis(
    origin_lat: float,
    origin_lon: float,
    dest_lat: float,
    dest_lon: float,
    language: str = "vi-VN"
) -> dict:
    """Get best route A→B and check for heavy traffic sections using TomTom Routing API."""
    try:
        import httpx
        api_key = os.getenv("TOMTOM_API_KEY")
        if not api_key:
            return {"error": "TOMTOM_API_KEY not configured"}

        url = f"https://api.tomtom.com/routing/1/calculateRoute/{origin_lat},{origin_lon}:{dest_lat},{dest_lon}/json"
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

@mcp.tool()
async def test_map_tile(
    zoom: int = 0,
    x: int = 0,
    y: int = 0,
    view: str = "Unified"
) -> dict:
    """Test TomTom API key with map tile request."""
    try:
        import httpx
        api_key = os.getenv("TOMTOM_API_KEY")
        if not api_key:
            return {"error": "TOMTOM_API_KEY not configured"}

        url = f"https://api.tomtom.com/map/1/tile/basic/main/{zoom}/{x}/{y}.png"
        params = {
            "view": view,
            "key": api_key
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return {
                "status": "success",
                "status_code": response.status_code,
                "content_type": response.headers.get("content-type"),
                "content_length": len(response.content)
            }
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    # Run MCP server (FastMCP uses stdio by default)
    mcp.run()

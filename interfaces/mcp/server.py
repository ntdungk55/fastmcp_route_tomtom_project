
from dataclasses import asdict
from typing import Literal
from fastmcp import FastMCP  # pip install fastmcp
from app.di.container import Container
from app.domain.value_objects.latlon import LatLon
from app.domain.enums.travel_mode import TravelMode
from app.application.dto.calculate_route_dto import CalculateRouteCommand

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

if __name__ == "__main__":
    mcp.run()

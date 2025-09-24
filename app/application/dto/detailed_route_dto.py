from dataclasses import dataclass
from typing import Optional, List
from app.domain.enums.travel_mode import TravelMode


@dataclass(frozen=True)
class DetailedRouteRequest:
    """Request DTO for detailed route calculation between two addresses"""
    origin_address: str
    destination_address: str
    travel_mode: TravelMode = TravelMode.CAR
    country_set: str = "VN"
    language: str = "vi-VN"


@dataclass(frozen=True)
class RoutePoint:
    """Represents a point on the route"""
    lat: float
    lon: float
    address: Optional[str] = None


@dataclass(frozen=True)
class RouteInstruction:
    """Turn-by-turn instruction"""
    instruction: str
    distance_m: int
    duration_s: int
    point: RoutePoint
    maneuver: Optional[str] = None
    road_name: Optional[str] = None


@dataclass(frozen=True)
class RouteLeg:
    """Route leg information"""
    start_point: RoutePoint
    end_point: RoutePoint
    distance_m: int
    duration_s: int


@dataclass(frozen=True)
class GuidanceInfo:
    """Guidance information from TomTom API"""
    instructions: List[RouteInstruction]


@dataclass(frozen=True)
class DetailedRouteSummary:
    """Summary of the detailed route"""
    distance_m: int
    duration_s: int
    traffic_delay_s: int
    fuel_consumption_l: Optional[float] = None


@dataclass(frozen=True)
class DetailedRouteResponse:
    """Response DTO for detailed route calculation"""
    summary: DetailedRouteSummary
    instructions: List[RouteInstruction]
    waypoints: List[RoutePoint]
    origin: RoutePoint
    destination: RoutePoint
    traffic_sections: List[dict]
    guidance: GuidanceInfo
    legs: List[RouteLeg]
    route_geometry: Optional[List[RoutePoint]] = None

"""DTOs for detailed route feature."""

from dataclasses import dataclass, field
from typing import List, Optional
from app.domain.value_objects.latlon import LatLon


@dataclass
class DetailedRouteRequest:
    """Request DTO for detailed route calculation."""
    origin_address: str
    destination_address: str
    travel_mode: str = "car"
    country_set: str = "VN"
    language: str = "vi-VN"


@dataclass
class RoutePoint:
    """A point in the route with address info."""
    address: str
    name: Optional[str] = None
    lat: float = 0.0
    lon: float = 0.0


@dataclass
class TrafficCondition:
    """Traffic condition info for a segment."""
    description: str
    delay_minutes: int = 0
    severity: Optional[str] = None  # "light", "moderate", "heavy", "severe"


@dataclass
class RouteInstruction:
    """Turn-by-turn instruction."""
    step: int
    instruction: str
    distance_meters: int
    duration_seconds: int
    traffic_condition: Optional[TrafficCondition] = None


@dataclass
class RouteSection:
    """A section of the route with traffic info."""
    start_point_index: int
    end_point_index: int
    section_type: str
    traffic_condition: Optional[TrafficCondition] = None


@dataclass
class MainRoute:
    """Main route with detailed information."""
    summary: str
    total_distance_meters: int
    total_duration_seconds: int
    traffic_condition: Optional[TrafficCondition] = None
    instructions: List[RouteInstruction] = field(default_factory=list)
    sections: List[RouteSection] = field(default_factory=list)


@dataclass
class AlternativeRoute:
    """Alternative route option."""
    summary: str
    total_distance_meters: int
    total_duration_seconds: int
    traffic_condition: Optional[TrafficCondition] = None


@dataclass
class DetailedRouteResponse:
    """Response DTO for detailed route."""
    origin: RoutePoint
    destination: RoutePoint
    main_route: MainRoute
    alternative_routes: List[AlternativeRoute] = field(default_factory=list)
    travel_mode: str = "car"
    total_alternative_count: int = 0

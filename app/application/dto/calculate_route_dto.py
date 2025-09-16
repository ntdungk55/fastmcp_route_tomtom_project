
from dataclasses import dataclass
from typing import Optional, List
from app.domain.value_objects.latlon import LatLon
from app.domain.enums.travel_mode import TravelMode

@dataclass(frozen=True)
class RouteSummary:
    distance_m: int
    duration_s: int

@dataclass(frozen=True)
class RouteSection:
    kind: str
    start_index: int
    end_index: int

@dataclass(frozen=True)
class CalculateRouteCommand:
    origin: LatLon
    destination: LatLon
    travel_mode: TravelMode = TravelMode.CAR
    waypoints: Optional[List[LatLon]] = None

@dataclass(frozen=True)
class RoutePlan:
    summary: RouteSummary
    sections: list[RouteSection]


from dataclasses import dataclass, field

from app.domain.enums.travel_mode import TravelMode
from app.domain.value_objects.latlon import LatLon


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
class RouteInstruction:
    """Turn-by-turn instruction from TomTom guidance."""
    step: int
    message: str
    distance_in_meters: int
    duration_in_seconds: int

@dataclass(frozen=True)
class RouteGuidance:
    """Guidance section with turn-by-turn instructions."""
    instructions: list[RouteInstruction] = field(default_factory=list)

@dataclass(frozen=True)
class CalculateRouteCommand:
    origin: LatLon
    destination: LatLon
    travel_mode: TravelMode = TravelMode.CAR
    waypoints: list[LatLon] | None = None

@dataclass(frozen=True)
class RoutePlan:
    summary: RouteSummary
    sections: list[RouteSection]
    guidance: RouteGuidance = field(default_factory=lambda: RouteGuidance(instructions=[]))

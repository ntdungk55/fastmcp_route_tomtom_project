"""DTOs for traffic operations."""

from dataclasses import dataclass
from typing import Optional, Union

from app.domain.value_objects.latlon import LatLon
from app.domain.constants.api_constants import TravelModeConstants, RouteTypeConstants, LanguageConstants, CountryConstants


@dataclass(frozen=True)
class TrafficConditionCommandDTO:
    """Command to get traffic condition at a location."""
    location: LatLon
    zoom: int = 10


@dataclass(frozen=True)
class TrafficFlowDataDTO:
    """Traffic flow information."""
    current_speed: Optional[float] = None
    free_flow_speed: Optional[float] = None
    current_travel_time: Optional[int] = None
    free_flow_travel_time: Optional[int] = None
    confidence: Optional[float] = None


@dataclass(frozen=True)
class TrafficConditionResultDTO:
    """Result of traffic condition query."""
    location: LatLon
    flow_data: TrafficFlowDataDTO
    road_closure: Optional[bool] = None


@dataclass(frozen=True)
class RouteWithTrafficCommandDTO:
    """Command to get route with traffic information."""
    origin: LatLon
    destination: LatLon
    travel_mode: str = TravelModeConstants.MOTORCYCLE
    route_type: str = RouteTypeConstants.FASTEST
    max_alternatives: int = 1
    language: str = LanguageConstants.DEFAULT


@dataclass(frozen=True)
class ViaRouteCommandDTO:
    """Command to calculate route via intermediate point."""
    origin: LatLon
    via_point: LatLon
    destination: LatLon
    travel_mode: str = TravelModeConstants.MOTORCYCLE
    language: str = LanguageConstants.DEFAULT


@dataclass(frozen=True)
class TrafficAnalysisCommandDTO:
    """Command to analyze traffic on a route."""
    origin: LatLon
    destination: LatLon
    language: str = LanguageConstants.DEFAULT


@dataclass(frozen=True)
class TrafficSectionDTO:
    """Traffic information for a route section."""
    section_index: int
    condition: str  # FLOWING, SLOW, JAM, CLOSED, UNKNOWN
    start_index: int
    end_index: int
    delay_seconds: Optional[int] = None


@dataclass(frozen=True)
class TrafficAnalysisResultDTO:
    """Result of traffic analysis."""
    overall_status: str  # LIGHT_TRAFFIC, MODERATE_TRAFFIC, HEAVY_TRAFFIC
    traffic_score: float  # 0-100, higher = worse traffic
    conditions_count: dict[str, int]
    heavy_traffic_sections: list[TrafficSectionDTO]
    total_sections: int
    recommendations: list[str]


@dataclass(frozen=True)
class AddressTrafficCommandDTO:
    """Command to check traffic between two addresses."""
    origin_address: str
    destination_address: str
    country_set: str = CountryConstants.DEFAULT
    travel_mode: str = TravelModeConstants.CAR
    language: str = LanguageConstants.DEFAULT


@dataclass(frozen=True)
class AddressTrafficResultDTO:
    """Result of address-to-address traffic check."""
    origin_info: dict
    destination_info: dict
    route_summary: dict
    traffic_analysis: TrafficAnalysisResultDTO

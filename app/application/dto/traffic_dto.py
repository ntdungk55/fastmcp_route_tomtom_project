"""DTOs cho Traffic Processing feature."""

from dataclasses import dataclass
from typing import List, Optional
from app.domain.value_objects.latlon import LatLon


@dataclass
class TrafficCheckCommand:
    """Command để kiểm tra tình trạng giao thông."""
    origin: LatLon
    destination: LatLon
    travel_mode: str = "car"
    language: str = "vi-VN"


@dataclass
class TrafficSection:
    """Thông tin một đoạn đường có giao thông tắc đường."""
    section_type: str
    start_point_index: int
    end_point_index: int
    simple_category: str
    effective_speed_kmh: float
    delay_seconds: int
    magnitude_of_delay: int
    event_id: Optional[str] = None


@dataclass
class TrafficResponse:
    """Response từ traffic checking service."""
    success: bool
    traffic_sections: List[TrafficSection]
    total_delay_seconds: int
    total_traffic_length_meters: int
    error_message: Optional[str] = None


@dataclass
class ReverseGeocodeCommand:
    """Command để reverse geocode coordinates."""
    coordinates: List[LatLon]
    language: str = "vi-VN"


@dataclass
class GeocodedAddress:
    """Địa chỉ đã được geocode."""
    coordinate: LatLon
    address: str
    freeform_address: str


@dataclass
class ReverseGeocodeResponse:
    """Response từ reverse geocoding service."""
    success: bool
    addresses: List[GeocodedAddress]
    error_message: Optional[str] = None


@dataclass
class TrafficSectionsCommand:
    """Command để xử lý traffic sections."""
    route_data: dict
    request_context: dict


@dataclass
class JamPair:
    """Cặp điểm bắt đầu và kết thúc của đoạn tắc đường."""
    section_index: int
    start: LatLon
    end: LatLon
    start_address: str
    end_address: str


@dataclass
class TrafficSectionsResponse:
    """Response từ traffic sections processing."""
    success: bool
    jam_pairs: List[JamPair]
    route_summary: dict
    guidance: dict
    metadata: dict
    error_message: Optional[str] = None


# DTOs for existing traffic-related tools
@dataclass
class AddressTrafficCommandDTO:
    """Command để check traffic giữa hai địa chỉ."""
    origin_address: str
    destination_address: str
    country_set: str = "VN"
    travel_mode: str = "car"
    language: str = "vi-VN"


@dataclass
class AddressTrafficResultDTO:
    """Result từ address traffic check."""
    origin: dict
    destination: dict
    traffic_analysis: dict


@dataclass
class RouteWithTrafficCommandDTO:
    """Command để lấy route với traffic."""
    origin: LatLon
    destination: LatLon
    travel_mode: str = "car"
    route_type: str = "fastest"
    max_alternatives: int = 0
    language: str = "vi-VN"


@dataclass
class TrafficAnalysisCommandDTO:
    """Command để analyze traffic trên route."""
    origin: LatLon
    destination: LatLon
    language: str = "vi-VN"


@dataclass
class TrafficConditionCommandDTO:
    """Command để lấy traffic condition tại location."""
    location: LatLon
    zoom: int = 10


@dataclass
class ViaRouteCommandDTO:
    """Command để lấy route đi qua via point."""
    origin: LatLon
    via_point: LatLon
    destination: LatLon
    travel_mode: str = "car"
    language: str = "vi-VN"


@dataclass
class TrafficAnalysisResultDTO:
    """Result từ traffic analysis."""
    route_summary: dict
    traffic_data: dict
    severe_delays: List[dict]
    recommendations: List[str]


@dataclass
class TrafficConditionResultDTO:
    """Result từ traffic condition check."""
    location: LatLon
    flow_data: dict
    road_closure: bool


@dataclass
class RouteSummary:
    """Route summary."""
    distance_m: int
    duration_s: int


@dataclass
class RouteSection:
    """Route section."""
    kind: str
    start_index: int
    end_index: int
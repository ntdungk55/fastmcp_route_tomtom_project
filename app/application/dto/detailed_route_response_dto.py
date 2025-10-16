"""
Detailed Route Response DTO - Model trả về cho get_detailed_route
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime


@dataclass
class RoutePoint:
    """Điểm trên tuyến đường."""
    name: str
    address: str
    lat: float
    lon: float


@dataclass
class TrafficCondition:
    """Trạng thái giao thông."""
    condition: str  # "light", "moderate", "heavy", "congested"
    delay_minutes: int
    description: str


@dataclass
class RouteInstruction:
    """Hướng dẫn chi tiết từng bước."""
    step: int
    instruction: str
    distance_meters: int
    duration_seconds: int
    road_name: Optional[str] = None
    traffic_condition: Optional[TrafficCondition] = None
    coordinates: Optional[Dict[str, float]] = None


@dataclass
class AlternativeRoute:
    """Tuyến đường thay thế."""
    route_id: str
    summary: str
    total_distance_meters: int
    total_duration_seconds: int
    traffic_condition: TrafficCondition
    instructions: List[RouteInstruction]
    highlights: List[str]


@dataclass
class DetailedRouteResponse:
    """
    Response DTO cho get_detailed_route theo model yêu cầu:
    1. Tên điểm đến điểm đi
    2. Thời gian đi
    3. Cách di chuyển
    4. Hướng dẫn chi tiết (kèm trạng thái đường đi)
    5. Cách di chuyển khác (kèm trạng thái đường đi)
    """
    
    # 1. Tên điểm đến điểm đi
    origin: RoutePoint
    destination: RoutePoint
    
    # 2. Thời gian đi
    total_duration_seconds: int
    total_duration_formatted: str  # "15 giờ 30 phút"
    departure_time: Optional[str] = None
    arrival_time: Optional[str] = None
    
    # 3. Cách di chuyển
    travel_mode: str  # "car", "bicycle", "foot", etc.
    travel_mode_description: str  # "Ô tô", "Xe đạp", "Đi bộ"
    
    # 4. Hướng dẫn chi tiết (kèm trạng thái đường đi)
    main_route: AlternativeRoute
    
    # 5. Cách di chuyển khác (kèm trạng thái đường đi)
    alternative_routes: List[AlternativeRoute] = None
    
    # Metadata
    calculated_at: str = None
    request_id: Optional[str] = None
    
    def __post_init__(self):
        if self.calculated_at is None:
            self.calculated_at = datetime.utcnow().isoformat() + "Z"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON response."""
        return {
            # 1. Tên điểm đến điểm đi
            "origin": {
                "name": self.origin.name,
                "address": self.origin.address,
                "coordinates": self.origin.coordinates
            },
            "destination": {
                "name": self.destination.name,
                "address": self.destination.address,
                "coordinates": self.destination.coordinates
            },
            
            # 2. Thời gian đi
            "travel_time": {
                "total_seconds": self.total_duration_seconds,
                "formatted": self.total_duration_formatted,
                "departure_time": self.departure_time,
                "arrival_time": self.arrival_time
            },
            
            # 3. Cách di chuyển
            "travel_mode": {
                "mode": self.travel_mode,
                "description": self.travel_mode_description
            },
            
            # 4. Hướng dẫn chi tiết (kèm trạng thái đường đi)
            "main_route": {
                "route_id": self.main_route.route_id,
                "summary": self.main_route.summary,
                "total_distance_meters": self.main_route.total_distance_meters,
                "total_duration_seconds": self.main_route.total_duration_seconds,
                "traffic_condition": {
                    "condition": self.main_route.traffic_condition.condition,
                    "delay_minutes": self.main_route.traffic_condition.delay_minutes,
                    "description": self.main_route.traffic_condition.description
                },
                "instructions": [
                    {
                        "step": inst.step,
                        "instruction": inst.instruction,
                        "distance_meters": inst.distance_meters,
                        "duration_seconds": inst.duration_seconds,
                        "road_name": inst.road_name,
                        "traffic_condition": {
                            "condition": inst.traffic_condition.condition,
                            "delay_minutes": inst.traffic_condition.delay_minutes,
                            "description": inst.traffic_condition.description
                        } if inst.traffic_condition else None,
                        "coordinates": inst.coordinates
                    }
                    for inst in self.main_route.instructions
                ],
                "highlights": self.main_route.highlights
            },
            
            # 5. Cách di chuyển khác (kèm trạng thái đường đi)
            "alternative_routes": [
                {
                    "route_id": alt.route_id,
                    "summary": alt.summary,
                    "total_distance_meters": alt.total_distance_meters,
                    "total_duration_seconds": alt.total_duration_seconds,
                    "traffic_condition": {
                        "condition": alt.traffic_condition.condition,
                        "delay_minutes": alt.traffic_condition.delay_minutes,
                        "description": alt.traffic_condition.description
                    },
                    "instructions": [
                        {
                            "step": inst.step,
                            "instruction": inst.instruction,
                            "distance_meters": inst.distance_meters,
                            "duration_seconds": inst.duration_seconds,
                            "road_name": inst.road_name,
                            "traffic_condition": {
                                "condition": inst.traffic_condition.condition,
                                "delay_minutes": inst.traffic_condition.delay_minutes,
                                "description": inst.traffic_condition.description
                            } if inst.traffic_condition else None,
                            "coordinates": inst.coordinates
                        }
                        for inst in alt.instructions
                    ],
                    "highlights": alt.highlights
                }
                for alt in (self.alternative_routes or [])
            ],
            
            # Metadata
            "metadata": {
                "calculated_at": self.calculated_at,
                "request_id": self.request_id
            }
        }


# Factory functions
def create_route_point(name: str, address: str, lat: float, lon: float) -> RoutePoint:
    """Create RoutePoint."""
    return RoutePoint(
        name=name,
        address=address,
        lat=lat,
        lon=lon
    )


def create_traffic_condition(condition: str, delay_minutes: int, description: str) -> TrafficCondition:
    """Create TrafficCondition."""
    return TrafficCondition(
        condition=condition,
        delay_minutes=delay_minutes,
        description=description
    )


def create_route_instruction(step: int, instruction: str, distance_meters: int, 
                           duration_seconds: int, road_name: Optional[str] = None,
                           traffic_condition: Optional[TrafficCondition] = None,
                           coordinates: Optional[Dict[str, float]] = None) -> RouteInstruction:
    """Create RouteInstruction."""
    return RouteInstruction(
        step=step,
        instruction=instruction,
        distance_meters=distance_meters,
        duration_seconds=duration_seconds,
        road_name=road_name,
        traffic_condition=traffic_condition,
        coordinates=coordinates
    )


def create_alternative_route(route_id: str, summary: str, total_distance_meters: int,
                           total_duration_seconds: int, traffic_condition: TrafficCondition,
                           instructions: List[RouteInstruction], highlights: List[str]) -> AlternativeRoute:
    """Create AlternativeRoute."""
    return AlternativeRoute(
        route_id=route_id,
        summary=summary,
        total_distance_meters=total_distance_meters,
        total_duration_seconds=total_duration_seconds,
        traffic_condition=traffic_condition,
        instructions=instructions,
        highlights=highlights
    )

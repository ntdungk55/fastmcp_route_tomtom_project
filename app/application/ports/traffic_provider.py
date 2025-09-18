"""Port for traffic operations."""

from typing import Protocol

from app.application.dto.calculate_route_dto import RoutePlan
from app.application.dto.traffic_dto import (
    RouteWithTrafficCommandDTO,
    TrafficAnalysisCommandDTO,
    TrafficAnalysisResultDTO,
    TrafficConditionCommandDTO,
    TrafficConditionResultDTO,
    ViaRouteCommandDTO,
)


class TrafficProvider(Protocol):
    """Port for traffic-related operations."""
    
    async def get_traffic_condition(self, cmd: TrafficConditionCommandDTO) -> TrafficConditionResultDTO:
        """Get traffic condition at a specific location."""
        ...
    
    async def get_route_with_traffic(self, cmd: RouteWithTrafficCommandDTO) -> RoutePlan:
        """Get route with traffic information."""
        ...
    
    async def get_via_route(self, cmd: ViaRouteCommandDTO) -> RoutePlan:
        """Calculate route via intermediate point."""
        ...
    
    async def analyze_route_traffic(self, cmd: TrafficAnalysisCommandDTO) -> TrafficAnalysisResultDTO:
        """Analyze traffic conditions on a route."""
        ...

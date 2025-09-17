
from typing import Protocol

from app.application.dto.calculate_route_dto import CalculateRouteCommand, RoutePlan


class RoutingProvider(Protocol):
    async def calculate_route(self, cmd: CalculateRouteCommand) -> RoutePlan: ...

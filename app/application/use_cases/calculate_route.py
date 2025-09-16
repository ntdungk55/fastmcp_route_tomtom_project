
from app.application.ports.routing_provider import RoutingProvider
from app.application.dto.calculate_route_dto import CalculateRouteCommand, RoutePlan

class CalculateRoute:
    """Use case: calculate a route via the configured routing provider."""
    def __init__(self, routing: RoutingProvider):
        self._routing = routing

    async def handle(self, cmd: CalculateRouteCommand) -> RoutePlan:
        return await self._routing.calculate_route(cmd)

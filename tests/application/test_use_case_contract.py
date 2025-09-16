
import pytest
from dataclasses import dataclass
from app.application.dto.calculate_route_dto import (
    CalculateRouteCommand, RoutePlan, RouteSummary, RouteSection
)
from app.domain.value_objects.latlon import LatLon
from app.domain.enums.travel_mode import TravelMode
from app.application.use_cases.calculate_route import CalculateRoute
from app.application.ports.routing_provider import RoutingProvider

@dataclass
class DummyProvider(RoutingProvider):
    async def calculate_route(self, cmd: CalculateRouteCommand) -> RoutePlan:
        return RoutePlan(summary=RouteSummary(100, 10), sections=[RouteSection("demo", 0, 1)])

@pytest.mark.asyncio
async def test_use_case_calls_port_and_returns_plan():
    uc = CalculateRoute(DummyProvider())  # type: ignore[arg-type]
    cmd = CalculateRouteCommand(LatLon(0.0, 0.0), LatLon(1.0, 1.0), TravelMode.CAR)
    plan = await uc.handle(cmd)
    assert plan.summary.distance_m == 100
    assert plan.summary.duration_s == 10

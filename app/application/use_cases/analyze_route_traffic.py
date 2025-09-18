"""Use case for analyzing route traffic."""

from app.application.dto.traffic_dto import TrafficAnalysisCommandDTO, TrafficAnalysisResultDTO
from app.application.ports.traffic_provider import TrafficProvider


class AnalyzeRouteTraffic:
    """Use case: analyze traffic conditions on a route."""
    
    def __init__(self, traffic: TrafficProvider):
        self._traffic = traffic
    
    async def handle(self, cmd: TrafficAnalysisCommandDTO) -> TrafficAnalysisResultDTO:
        """Handle route traffic analysis."""
        return await self._traffic.analyze_route_traffic(cmd)

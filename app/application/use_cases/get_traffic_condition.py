"""Use case for getting traffic conditions."""

from app.application.dto.traffic_dto import TrafficConditionCommandDTO, TrafficConditionResultDTO
from app.application.ports.traffic_provider import TrafficProvider


class GetTrafficCondition:
    """Use case: get traffic condition at a location."""
    
    def __init__(self, traffic: TrafficProvider):
        self._traffic = traffic
    
    async def execute(self, cmd: TrafficConditionCommandDTO) -> TrafficConditionResultDTO:
        """Handle traffic condition query."""
        return await self._traffic.get_traffic_condition(cmd)

"""Traffic Provider Port - Interface cho traffic checking services."""

from typing import Protocol
from app.application.dto.traffic_dto import TrafficCheckCommand, TrafficResponse


class TrafficProvider(Protocol):
    """Interface cho traffic checking services.
    
    Chức năng: Kiểm tra tình trạng giao thông trên tuyến đường
    """
    
    async def check_severe_traffic(self, cmd: TrafficCheckCommand) -> TrafficResponse:
        """Kiểm tra tình trạng giao thông nghiêm trọng trên tuyến đường.
        
        Args:
            cmd: TrafficCheckCommand chứa thông tin tuyến đường cần kiểm tra
            
        Returns:
            TrafficResponse với thông tin traffic sections và mức độ nghiêm trọng
        """
        ...
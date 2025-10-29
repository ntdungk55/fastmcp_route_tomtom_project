"""Use Case cho Traffic Checking - BLK-1-15."""

from app.application.dto.traffic_dto import TrafficCheckCommand, TrafficResponse
from app.application.ports.traffic_provider import TrafficProvider
from app.infrastructure.logging.logger import get_logger

logger = get_logger(__name__)


class CheckTrafficUseCase:
    """Use Case để kiểm tra tình trạng giao thông.
    
    Chức năng: Orchestrate việc kiểm tra traffic từ external provider
    """
    
    def __init__(self, traffic_provider: TrafficProvider):
        """Khởi tạo use case với traffic provider."""
        self._traffic_provider = traffic_provider

    async def execute(self, cmd: TrafficCheckCommand) -> TrafficResponse:
        """Thực hiện kiểm tra tình trạng giao thông.
        
        Args:
            cmd: TrafficCheckCommand chứa thông tin tuyến đường
            
        Returns:
            TrafficResponse với kết quả kiểm tra traffic
        """
        try:
            logger.info(f"Checking traffic for route: {cmd.origin} -> {cmd.destination}")
            
            # Gọi traffic provider để kiểm tra
            response = await self._traffic_provider.check_severe_traffic(cmd)
            
            if response.success:
                logger.info(f"Traffic check completed: {len(response.traffic_sections)} sections found")
            else:
                logger.warning(f"Traffic check failed: {response.error_message}")
            
            return response
            
        except Exception as e:
            logger.error(f"Error in CheckTrafficUseCase: {e}")
            return TrafficResponse(
                success=False,
                traffic_sections=[],
                total_delay_seconds=0,
                total_traffic_length_meters=0,
                error_message=f"Use case error: {e}"
            )


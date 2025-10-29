"""Use Case cho Reverse Geocoding - BLK-1-17."""

from app.application.dto.traffic_dto import ReverseGeocodeCommand, ReverseGeocodeResponse
from app.application.ports.reverse_geocode_provider import ReverseGeocodeProvider
from app.infrastructure.logging.logger import get_logger

logger = get_logger(__name__)


class ReverseGeocodeUseCase:
    """Use Case để reverse geocode coordinates.
    
    Chức năng: Orchestrate việc reverse geocoding từ external provider
    """
    
    def __init__(self, reverse_geocode_provider: ReverseGeocodeProvider):
        """Khởi tạo use case với reverse geocode provider."""
        self._reverse_geocode_provider = reverse_geocode_provider

    async def execute(self, cmd: ReverseGeocodeCommand) -> ReverseGeocodeResponse:
        """Thực hiện reverse geocoding.
        
        Args:
            cmd: ReverseGeocodeCommand chứa coordinates cần geocode
            
        Returns:
            ReverseGeocodeResponse với kết quả geocoding
        """
        try:
            logger.info(f"Reverse geocoding {len(cmd.coordinates)} coordinates")
            
            # Gọi reverse geocode provider
            response = await self._reverse_geocode_provider.reverse_geocode(cmd)
            
            if response.success:
                logger.info(f"Reverse geocoding completed: {len(response.addresses)} addresses found")
            else:
                logger.warning(f"Reverse geocoding failed: {response.error_message}")
            
            return response
            
        except Exception as e:
            logger.error(f"Error in ReverseGeocodeUseCase: {e}")
            return ReverseGeocodeResponse(
                success=False,
                addresses=[],
                error_message=f"Use case error: {e}"
            )


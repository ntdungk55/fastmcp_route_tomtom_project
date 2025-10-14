"""Use case for searching destinations by name and/or address."""

from app.application.dto.search_destinations_dto import SearchDestinationsRequest, SearchDestinationsResponse, DestinationSummary
from app.application.ports.destination_repository import DestinationRepository
from app.infrastructure.logging.logger import get_logger

logger = get_logger(__name__)


class SearchDestinationsUseCase:
    """Use case: search destinations by name and/or address."""
    
    def __init__(self, destination_repository: DestinationRepository):
        self._destination_repository = destination_repository
    
    async def execute(self, request: SearchDestinationsRequest) -> SearchDestinationsResponse:
        """Execute search destinations by name and/or address."""
        try:
            logger.info(f"Searching destinations with name='{request.name}', address='{request.address}'")
            
            # Nếu tất cả parameters đều None, lấy tất cả destinations (list all)
            # Không cần validation vì có thể list all destinations
            
            # Search destinations using repository
            destinations = await self._destination_repository.search_by_name_and_address(
                id=request.id,
                name=request.name,
                address=request.address
            )
            
            # Convert to DTOs
            destination_summaries = [
                DestinationSummary(
                    id=dest.id or "",
                    name=dest.name.value,
                    address=dest.address.value,
                    latitude=dest.coordinates.lat,
                    longitude=dest.coordinates.lon,
                    created_at=dest.created_at.isoformat(),
                    updated_at=dest.updated_at.isoformat()
                )
                for dest in destinations
            ]
            
            logger.info(f"Found {len(destination_summaries)} destinations matching search criteria")
            
            return SearchDestinationsResponse(
                success=True,
                destinations=destination_summaries,
                total_count=len(destination_summaries),
                message=f"Tìm thấy {len(destination_summaries)} điểm đến khớp với tiêu chí tìm kiếm"
            )
            
        except Exception as e:
            logger.error(f"Error searching destinations: {str(e)}")
            return SearchDestinationsResponse(
                success=False,
                destinations=[],
                total_count=0,
                message="Lỗi khi tìm kiếm điểm đến",
                error=str(e)
            )

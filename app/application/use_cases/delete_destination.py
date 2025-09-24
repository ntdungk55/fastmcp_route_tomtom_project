"""Use case for deleting a destination."""

from app.application.dto.delete_destination_dto import DeleteDestinationRequest, DeleteDestinationResponse
from app.application.ports.destination_repository import DestinationRepository
from app.infrastructure.logging.logger import get_logger

logger = get_logger(__name__)


class DeleteDestinationUseCase:
    """Use case for deleting a destination."""
    
    def __init__(self, destination_repository: DestinationRepository):
        self._destination_repository = destination_repository
    
    async def execute(self, request: DeleteDestinationRequest) -> DeleteDestinationResponse:
        """Execute delete destination use case."""
        try:
            logger.info(f"Deleting destination with ID: {request.destination_id}")
            
            # Check if destination exists
            existing_destination = await self._destination_repository.find_by_id(request.destination_id)
            if not existing_destination:
                return DeleteDestinationResponse(
                    success=False,
                    deleted=False,
                    error=f"Destination with ID '{request.destination_id}' not found"
                )
            
            # Delete destination
            deleted = await self._destination_repository.delete(request.destination_id)
            
            if deleted:
                logger.info(f"Successfully deleted destination with ID: {request.destination_id}")
                return DeleteDestinationResponse(
                    success=True,
                    deleted=True,
                    message=f"Destination '{existing_destination.name}' deleted successfully"
                )
            else:
                return DeleteDestinationResponse(
                    success=False,
                    deleted=False,
                    error="Failed to delete destination"
                )
                
        except Exception as e:
            logger.error(f"Error deleting destination: {str(e)}")
            return DeleteDestinationResponse(
                success=False,
                deleted=False,
                error=f"Failed to delete destination: {str(e)}"
            )

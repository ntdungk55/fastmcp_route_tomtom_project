"""Use case for listing all destinations."""

from typing import List
from datetime import datetime

from app.application.dto.list_destinations_dto import (
    ListDestinationsRequest, 
    ListDestinationsResponse, 
    DestinationSummary
)
from app.application.ports.destination_repository import DestinationRepository
from app.infrastructure.logging.logger import get_logger

logger = get_logger(__name__)


class ListDestinationsUseCase:
    """Use case for listing all destinations."""
    
    def __init__(self, destination_repository: DestinationRepository):
        self._destination_repository = destination_repository
    
    async def execute(self, request: ListDestinationsRequest) -> ListDestinationsResponse:
        """Execute list destinations use case."""
        try:
            logger.info("Listing all destinations")
            
            # Get all destinations from repository
            destinations = await self._destination_repository.list_all()
            
            # Convert to summary DTOs
            destination_summaries = []
            for dest in destinations:
                summary = DestinationSummary(
                    id=dest.id,
                    name=dest.name,
                    address=dest.address,
                    latitude=dest.coordinates.lat,
                    longitude=dest.coordinates.lon,
                    created_at=dest.created_at.isoformat(),
                    updated_at=dest.updated_at.isoformat()
                )
                destination_summaries.append(summary)
            
            logger.info(f"Found {len(destination_summaries)} destinations")
            
            return ListDestinationsResponse(
                success=True,
                destinations=destination_summaries,
                total_count=len(destination_summaries),
                message=f"Found {len(destination_summaries)} destinations"
            )
            
        except Exception as e:
            logger.error(f"Error listing destinations: {str(e)}")
            return ListDestinationsResponse(
                success=False,
                destinations=[],
                total_count=0,
                error=f"Failed to list destinations: {str(e)}"
            )

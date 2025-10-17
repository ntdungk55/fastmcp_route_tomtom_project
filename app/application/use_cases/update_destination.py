"""Use case for updating a destination."""

from typing import Optional
from datetime import datetime, timezone

from app.application.dto.update_destination_dto import UpdateDestinationRequest, UpdateDestinationResponse
from app.application.dto.geocoding_dto import GeocodeAddressCommandDTO
from app.application.ports.destination_repository import DestinationRepository
from app.application.ports.geocoding_provider import GeocodingProvider
from app.domain.entities.destination import Destination
from app.domain.value_objects.latlon import LatLon
from app.domain.value_objects.destination_name import DestinationName
from app.domain.value_objects.address import Address
from app.infrastructure.logging.logger import get_logger

logger = get_logger(__name__)


class UpdateDestinationUseCase:
    """Use case for updating a destination."""
    
    def __init__(self, destination_repository: DestinationRepository, geocoding_provider: GeocodingProvider):
        self._destination_repository = destination_repository
        self._geocoding_provider = geocoding_provider
    
    async def execute(self, request: UpdateDestinationRequest) -> UpdateDestinationResponse:
        """Execute update destination use case."""
        try:
            logger.info(f"Updating destination with ID: {request.destination_id}")
            
            # Check if destination exists
            existing_destination = await self._destination_repository.find_by_id(request.destination_id)
            if not existing_destination:
                return UpdateDestinationResponse(
                    success=False,
                    error=f"Destination with ID '{request.destination_id}' not found"
                )
            
            # Prepare update data - keep existing value objects
            new_name = existing_destination.name
            new_address = existing_destination.address
            new_coordinates = existing_destination.coordinates
            
            # If address is being updated, geocode it
            if request.address is not None and request.address.strip() != str(existing_destination.address):
                logger.info(f"Geocoding new address: {request.address}")
                from app.application.constants.validation_constants import DefaultValues
                geocode_cmd = GeocodeAddressCommandDTO(
                    address=request.address,
                    country_set=DefaultValues.DEFAULT_COUNTRY,
                    limit=DefaultValues.DEFAULT_LIMIT,
                    language=DefaultValues.DEFAULT_LANGUAGE
                )
                
                geocode_result = await self._geocoding_provider.geocode_address(geocode_cmd)
                
                if not geocode_result.results or len(geocode_result.results) == 0:
                    return UpdateDestinationResponse(
                        success=False,
                        error=f"Could not find coordinates for address: {request.address}"
                    )
                
                # Get first result
                first_result = geocode_result.results[0]
                new_coordinates = LatLon(first_result.position.lat, first_result.position.lon)
                new_address = Address(request.address.strip())
                logger.info(f"Found new coordinates: {new_coordinates.lat}, {new_coordinates.lon}")
            
            # Check for name conflicts if name is being updated
            if request.name is not None and request.name.strip() != str(existing_destination.name):
                existing_by_name = await self._destination_repository.find_by_name(request.name)
                if existing_by_name and existing_by_name.id != request.destination_id:
                    return UpdateDestinationResponse(
                        success=False,
                        error=f"Destination with name '{request.name}' already exists"
                    )
                new_name = DestinationName(request.name.strip())
            
            # Create updated destination (immutable pattern - do NOT mutate existing)
            updated_destination = Destination(
                id=existing_destination.id,
                name=new_name,
                address=new_address,
                coordinates=new_coordinates,
                created_at=existing_destination.created_at,
                updated_at=datetime.now(timezone.utc)
            )
            
            # Save updated destination
            saved_destination = await self._destination_repository.save(updated_destination)
            
            logger.info(f"Successfully updated destination with ID: {saved_destination.id}")
            
            # Verify that the destination was actually updated in database
            logger.info(f"Verifying destination was updated in database...")
            if saved_destination.id is None:
                logger.error("❌ Database verification failed - destination ID is None")
                return UpdateDestinationResponse(
                    success=False,
                    error="Database verification failed - destination ID is None"
                )
            
            verification_destination = await self._destination_repository.find_by_id(saved_destination.id)
            
            if verification_destination:
                logger.info("✅ Database verification successful - destination found in database")
                return UpdateDestinationResponse(
                    success=True,
                    destination_id=saved_destination.id,
                    message=f"Destination '{saved_destination.name}' updated successfully"
                )
            else:
                logger.error("❌ Database verification failed - destination not found in database")
                return UpdateDestinationResponse(
                    success=False,
                    error="Database verification failed - destination was not updated properly"
                )
            
        except Exception as e:
            logger.error(f"Error updating destination: {str(e)}")
            return UpdateDestinationResponse(
                success=False,
                error=f"Failed to update destination: {str(e)}"
            )

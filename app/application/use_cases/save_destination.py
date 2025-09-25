from typing import Optional
from datetime import datetime, timezone
import uuid

from app.application.dto.save_destination_dto import SaveDestinationRequest, SaveDestinationResponse
from app.application.dto.geocoding_dto import GeocodeAddressCommandDTO
from app.application.ports.destination_repository import DestinationRepository
from app.application.ports.geocoding_provider import GeocodingProvider
from app.domain.entities.destination import Destination
from app.domain.value_objects.latlon import LatLon
from app.infrastructure.logging.logger import get_logger

logger = get_logger(__name__)


class SaveDestinationUseCase:
    """Use case for saving a destination"""
    
    def __init__(self, destination_repository: DestinationRepository, geocoding_provider: GeocodingProvider):
        self._destination_repository = destination_repository
        self._geocoding_provider = geocoding_provider
    
    async def execute(self, request: SaveDestinationRequest) -> SaveDestinationResponse:
        """Execute save destination use case"""
        try:
            logger.info(f"Saving destination: {request.name}")
            
            # Check if destination with same name already exists
            existing_destination = await self._destination_repository.find_by_name(request.name)
            if existing_destination:
                return SaveDestinationResponse(
                    success=False,
                    error=f"Destination with name '{request.name}' already exists"
                )
            
            # Geocode address to get coordinates
            logger.info(f"Geocoding address: {request.address}")
            from app.application.constants.validation_constants import DefaultValues
            geocode_cmd = GeocodeAddressCommandDTO(
                address=request.address,
                country_set=DefaultValues.DEFAULT_COUNTRY,
                limit=DefaultValues.DEFAULT_LIMIT,
                language=DefaultValues.DEFAULT_LANGUAGE
            )
            
            geocode_result = await self._geocoding_provider.geocode_address(geocode_cmd)
            
            if not geocode_result.results or len(geocode_result.results) == 0:
                return SaveDestinationResponse(
                    success=False,
                    error=f"Could not find coordinates for address: {request.address}"
                )
            
            # Get first result
            first_result = geocode_result.results[0]
            coordinates = LatLon(first_result.position.lat, first_result.position.lon)
            
            logger.info(f"Found coordinates: {coordinates.lat}, {coordinates.lon}")
            
            # Create destination entity
            now = datetime.now(timezone.utc)
            destination = Destination(
                id=None,  # Will be set by repository
                name=request.name.strip(),
                address=request.address.strip(),
                coordinates=coordinates,
                created_at=now,
                updated_at=now
            )
            
            # Save destination
            saved_destination = await self._destination_repository.save(destination)
            
            logger.info(f"Successfully saved destination with ID: {saved_destination.id}")
            
            # Verify that the destination was actually saved to database
            logger.info(f"Verifying destination was saved to database...")
            if saved_destination.id is None:
                logger.error("❌ Database verification failed - destination ID is None")
                return SaveDestinationResponse(
                    success=False,
                    error="Database verification failed - destination ID is None"
                )
            
            verification_destination = await self._destination_repository.find_by_id(saved_destination.id)
            
            if verification_destination:
                logger.info("✅ Database verification successful - destination found in database")
                return SaveDestinationResponse(
                    success=True,
                    destination_id=saved_destination.id,
                    message=f"Destination '{request.name}' saved successfully at {coordinates.lat}, {coordinates.lon}"
                )
            else:
                logger.error("❌ Database verification failed - destination not found in database")
                return SaveDestinationResponse(
                    success=False,
                    error="Database verification failed - destination was not saved properly"
                )
            
        except ValueError as e:
            logger.error(f"Validation error: {str(e)}")
            return SaveDestinationResponse(
                success=False,
                error=f"Validation error: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Error saving destination: {str(e)}")
            return SaveDestinationResponse(
                success=False,
                error=f"Failed to save destination: {str(e)}"
            )

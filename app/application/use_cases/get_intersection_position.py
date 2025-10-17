"""Use case for getting intersection positions."""

from app.application.dto.geocoding_dto import GeocodeResponseDTO, StructuredGeocodeCommandDTO
from app.application.ports.geocoding_provider import GeocodingProvider


class GetIntersectionPosition:
    """Use case: get intersection position using structured geocoding."""
    
    def __init__(self, geocoding: GeocodingProvider):
        self._geocoding = geocoding
    
    async def execute(self, cmd: StructuredGeocodeCommandDTO) -> GeocodeResponseDTO:
        """Handle structured geocoding command for intersections."""
        return await self._geocoding.structured_geocode(cmd)

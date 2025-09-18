"""Use case for getting street center positions."""

from app.application.dto.geocoding_dto import GeocodeResponseDTO
from app.application.ports.geocoding_provider import GeocodingProvider


class GetStreetCenter:
    """Use case: get street center position."""
    
    def __init__(self, geocoding: GeocodingProvider):
        self._geocoding = geocoding
    
    async def handle(
        self, 
        street_name: str, 
        country_set: str = "VN",
        language: str = "vi-VN"
    ) -> GeocodeResponseDTO:
        """Handle getting street center position."""
        return await self._geocoding.search_street_center(
            street_name, country_set, language
        )

"""Use case for getting street center positions."""

from app.application.dto.geocoding_dto import GeocodeResponseDTO
from app.application.ports.geocoding_provider import GeocodingProvider
from app.domain.constants.api_constants import CountryConstants


class GetStreetCenter:
    """Use case: get street center position."""
    
    def __init__(self, geocoding: GeocodingProvider):
        self._geocoding = geocoding
    
    async def handle(
        self, 
        street_name: str, 
        country_set: str = CountryConstants.DEFAULT,
        language: str = None
    ) -> GeocodeResponseDTO:
        """Handle getting street center position."""
        if language is None:
            from app.application.constants.validation_constants import DefaultValues
            language = DefaultValues.DEFAULT_LANGUAGE
        return await self._geocoding.search_street_center(
            street_name, country_set, language
        )

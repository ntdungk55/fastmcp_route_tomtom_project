"""Use case for geocoding addresses."""

from app.application.dto.geocoding_dto import GeocodeAddressCommandDTO, GeocodeResponseDTO
from app.application.ports.geocoding_provider import GeocodingProvider


class GeocodeAddress:
    """Use case: geocode an address to coordinates."""
    
    def __init__(self, geocoding: GeocodingProvider):
        self._geocoding = geocoding
    
    async def handle(self, cmd: GeocodeAddressCommandDTO) -> GeocodeResponseDTO:
        """Handle geocoding address command."""
        return await self._geocoding.geocode_address(cmd)

"""Port for geocoding operations."""

from typing import Protocol

from app.application.dto.geocoding_dto import (
    GeocodeAddressCommandDTO,
    GeocodeResponseDTO,
    StructuredGeocodeCommandDTO,
)


class GeocodingProvider(Protocol):
    """Port for geocoding operations."""
    
    async def geocode_address(self, cmd: GeocodeAddressCommandDTO) -> GeocodeResponseDTO:
        """Geocode an address to coordinates."""
        ...
    
    async def structured_geocode(self, cmd: StructuredGeocodeCommandDTO) -> GeocodeResponseDTO:
        """Structured geocoding for intersections."""
        ...
    
    async def search_street_center(
        self, 
        street_name: str, 
        country_set: str = "VN",
        language: str = "vi-VN"
    ) -> GeocodeResponseDTO:
        """Get street center position."""
        ...

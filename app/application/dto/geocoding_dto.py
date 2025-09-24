"""DTOs for geocoding operations."""

from dataclasses import dataclass
from typing import Optional

from app.domain.value_objects.latlon import LatLon
from app.domain.constants.api_constants import CountryConstants, LanguageConstants


@dataclass(frozen=True)
class GeocodeAddressCommandDTO:
    """Command to geocode an address to coordinates."""
    address: str
    country_set: str = CountryConstants.DEFAULT
    limit: int = 1
    language: str = LanguageConstants.DEFAULT


@dataclass(frozen=True)
class AddressDTO:
    """Address information."""
    freeform_address: str
    country: Optional[str] = None
    country_code: Optional[str] = None
    municipality: Optional[str] = None
    street_name: Optional[str] = None


@dataclass(frozen=True)
class GeocodingResultDTO:
    """Result of geocoding operation."""
    position: LatLon
    address: AddressDTO
    confidence: Optional[float] = None


@dataclass(frozen=True)
class GeocodeResponseDTO:
    """Response containing geocoding results."""
    results: list[GeocodingResultDTO]
    summary: Optional[dict] = None


@dataclass(frozen=True)
class StructuredGeocodeCommandDTO:
    """Command for structured geocoding (intersections)."""
    street_name: str
    cross_street: str
    municipality: str
    country_code: str = CountryConstants.DEFAULT
    limit: int = 1
    language: str = LanguageConstants.DEFAULT

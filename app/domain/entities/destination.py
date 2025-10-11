from dataclasses import dataclass
from typing import Optional
from datetime import datetime, timezone
from app.domain.value_objects.latlon import LatLon
from app.domain.value_objects.destination_name import DestinationName
from app.domain.value_objects.address import Address
from app.domain.errors import (
    EmptyNameError, 
    EmptyAddressError, 
    InvalidDateTimeError,
    InvalidCoordinateError
)


@dataclass
class Destination:
    """Entity representing a saved destination with comprehensive validation"""
    id: Optional[str]
    name: DestinationName
    address: Address
    coordinates: LatLon
    created_at: datetime
    updated_at: datetime
    
    def __post_init__(self):
        """Validate entity after initialization with comprehensive rules"""
        self._validate_name()
        self._validate_address()
        self._validate_coordinates()
        self._validate_datetimes()
    
    def _validate_name(self) -> None:
        """Validate destination name"""
        if not isinstance(self.name, DestinationName):
            raise EmptyNameError(
                "Name must be a DestinationName value object",
                entity_id=self.id or "unknown",
                field="name",
                value=self.name
            )
    
    def _validate_address(self) -> None:
        """Validate destination address"""
        if not isinstance(self.address, Address):
            raise EmptyAddressError(
                "Address must be an Address value object",
                entity_id=self.id or "unknown",
                field="address",
                value=self.address
            )
    
    def _validate_coordinates(self) -> None:
        """Validate coordinates"""
        if not isinstance(self.coordinates, LatLon):
            raise InvalidCoordinateError(
                "Coordinates must be a LatLon value object",
                entity_id=self.id or "unknown",
                field="coordinates",
                value=self.coordinates
            )
        
        # LatLon value object already validates lat/lon ranges
        # Additional validation can be added here if needed
    
    def _validate_datetimes(self) -> None:
        """Validate datetime fields"""
        if not isinstance(self.created_at, datetime):
            raise InvalidDateTimeError("created_at must be a datetime object")
        
        if not isinstance(self.updated_at, datetime):
            raise InvalidDateTimeError("updated_at must be a datetime object")
        
        if self.updated_at < self.created_at:
            raise InvalidDateTimeError("updated_at cannot be earlier than created_at")
        
        # Check if datetimes are not too far in the future (reasonable business rule)
        now = datetime.now(timezone.utc)
        if self.created_at > now:
            raise InvalidDateTimeError("created_at cannot be in the future")
        
        if self.updated_at > now:
            raise InvalidDateTimeError("updated_at cannot be in the future")
    
    def update_name(self, new_name: str) -> None:
        """Update destination name with validation"""
        self.name = DestinationName(new_name)
        self.updated_at = datetime.now(timezone.utc)
    
    def update_address(self, new_address: str) -> None:
        """Update destination address with validation"""
        self.address = Address(new_address)
        self.updated_at = datetime.now(timezone.utc)
    
    def update_coordinates(self, new_coordinates: LatLon) -> None:
        """Update destination coordinates with validation"""
        if not isinstance(new_coordinates, LatLon):
            raise InvalidCoordinateError("Coordinates must be a LatLon value object")
        
        self.coordinates = new_coordinates
        self.updated_at = datetime.now(timezone.utc)

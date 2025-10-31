from dataclasses import dataclass
from typing import Optional
from app.domain.errors import DomainError


class InvalidLocationNameError(DomainError):
    """Raised when location name is invalid."""
    pass


@dataclass(frozen=True)
class LocationName:
    """Value object for location name with validation."""
    value: str
    country: Optional[str] = None
    
    def __post_init__(self) -> None:
        """Validate location name."""
        if not self.value:
            raise InvalidLocationNameError(
                "Location name cannot be None or empty",
                entity_id="location_name",
                field="value",
                value=self.value
            )
        
        name_trimmed = self.value.strip()
        if not name_trimmed:
            raise InvalidLocationNameError(
                "Location name cannot be empty or whitespace only",
                entity_id="location_name",
                field="value",
                value=self.value
            )
        
        if len(name_trimmed) > 200:
            raise InvalidLocationNameError(
                "Location name cannot exceed 200 characters",
                entity_id="location_name",
                field="value",
                value=self.value
            )
        
        # Update the value with trimmed version
        object.__setattr__(self, 'value', name_trimmed)
        
        # Validate country if provided
        if self.country is not None:
            country_trimmed = self.country.strip()
            if len(country_trimmed) > 100:
                raise InvalidLocationNameError(
                    "Country name cannot exceed 100 characters",
                    entity_id="location_name",
                    field="country",
                    value=self.country
                )
            object.__setattr__(self, 'country', country_trimmed)
    
    def __str__(self) -> str:
        """String representation."""
        if self.country:
            return f"{self.value}, {self.country}"
        return self.value
    
    def __eq__(self, other) -> bool:
        """Equality comparison."""
        if not isinstance(other, LocationName):
            return False
        return self.value.lower() == other.value.lower() and self.country == other.country
    
    def __hash__(self) -> int:
        """Hash for use in sets and dicts."""
        return hash((self.value.lower(), self.country))




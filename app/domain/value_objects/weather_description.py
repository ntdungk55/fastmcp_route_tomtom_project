from dataclasses import dataclass
from app.domain.errors import DomainError


class InvalidWeatherDescriptionError(DomainError):
    """Raised when weather description is invalid."""
    pass


@dataclass(frozen=True)
class WeatherDescription:
    """Value object for weather description with validation."""
    value: str
    
    def __post_init__(self) -> None:
        """Validate weather description."""
        if not self.value:
            raise InvalidWeatherDescriptionError(
                "Weather description cannot be None or empty",
                entity_id="weather_description",
                field="value",
                value=self.value
            )
        
        description_trimmed = self.value.strip()
        if not description_trimmed:
            raise InvalidWeatherDescriptionError(
                "Weather description cannot be empty or whitespace only",
                entity_id="weather_description",
                field="value",
                value=self.value
            )
        
        if len(description_trimmed) > 200:
            raise InvalidWeatherDescriptionError(
                "Weather description cannot exceed 200 characters",
                entity_id="weather_description",
                field="value",
                value=self.value
            )
        
        # Update the value with trimmed version
        object.__setattr__(self, 'value', description_trimmed)
    
    def __str__(self) -> str:
        """String representation."""
        return self.value
    
    def __eq__(self, other) -> bool:
        """Equality comparison."""
        if not isinstance(other, WeatherDescription):
            return False
        return self.value.lower() == other.value.lower()
    
    def __hash__(self) -> int:
        """Hash for use in sets and dicts."""
        return hash(self.value.lower())





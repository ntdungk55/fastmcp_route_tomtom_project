from dataclasses import dataclass
from app.domain.errors import DomainError


class InvalidWeatherUnitsError(DomainError):
    """Raised when weather units are invalid."""
    pass


@dataclass(frozen=True)
class WeatherUnits:
    """Value object for weather measurement units."""
    value: str  # "metric", "imperial", "kelvin"
    
    def __post_init__(self) -> None:
        """Validate weather units."""
        valid_units = ["metric", "imperial", "kelvin"]
        if self.value not in valid_units:
            raise InvalidWeatherUnitsError(
                f"Invalid weather units: {self.value}. Must be one of: {valid_units}",
                entity_id="weather_units",
                field="value",
                value=self.value
            )
    
    @property
    def temperature_symbol(self) -> str:
        """Get temperature symbol for this unit."""
        if self.value == "metric":
            return "°C"
        elif self.value == "imperial":
            return "°F"
        elif self.value == "kelvin":
            return "K"
        return ""
    
    @property
    def speed_unit(self) -> str:
        """Get speed unit for this unit system."""
        if self.value == "metric" or self.value == "kelvin":
            return "m/s"
        elif self.value == "imperial":
            return "mph"
        return ""
    
    @property
    def distance_unit(self) -> str:
        """Get distance unit for this unit system."""
        if self.value == "metric" or self.value == "kelvin":
            return "m"
        elif self.value == "imperial":
            return "ft"
        return ""
    
    def __str__(self) -> str:
        """String representation."""
        return self.value
    
    def __eq__(self, other) -> bool:
        """Equality comparison."""
        if not isinstance(other, WeatherUnits):
            return False
        return self.value == other.value
    
    def __hash__(self) -> int:
        """Hash for use in sets and dicts."""
        return hash(self.value)





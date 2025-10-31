from dataclasses import dataclass
from app.domain.errors import DomainError


class InvalidTemperatureError(DomainError):
    """Raised when temperature value is invalid."""
    pass


@dataclass(frozen=True)
class Temperature:
    """Value object for temperature with validation."""
    value: float
    units: str  # "metric", "imperial", "kelvin"
    
    def __post_init__(self) -> None:
        """Validate temperature value based on units."""
        # Validate units
        valid_units = ["metric", "imperial", "kelvin"]
        if self.units not in valid_units:
            raise InvalidTemperatureError(
                f"Invalid temperature units: {self.units}. Must be one of: {valid_units}",
                entity_id="temperature",
                field="units",
                value=self.units
            )
        
        # Validate temperature range based on units
        if self.units == "metric":  # Celsius
            if not (-273.15 <= self.value <= 100.0):
                # Allow up to 100°C (reasonable maximum)
                if self.value < -273.15:
                    raise InvalidTemperatureError(
                        f"Temperature cannot be below absolute zero: {self.value}°C",
                        entity_id="temperature",
                        field="value",
                        value=self.value
                    )
        elif self.units == "imperial":  # Fahrenheit
            if not (-459.67 <= self.value <= 212.0):
                # Allow up to 212°F (boiling point)
                if self.value < -459.67:
                    raise InvalidTemperatureError(
                        f"Temperature cannot be below absolute zero: {self.value}°F",
                        entity_id="temperature",
                        field="value",
                        value=self.value
                    )
        elif self.units == "kelvin":
            if not (0.0 <= self.value <= 373.15):
                # Allow up to 373.15K (100°C)
                if self.value < 0.0:
                    raise InvalidTemperatureError(
                        f"Temperature in Kelvin cannot be negative: {self.value}K",
                        entity_id="temperature",
                        field="value",
                        value=self.value
                    )
    
    def to_celsius(self) -> float:
        """Convert temperature to Celsius."""
        if self.units == "metric":
            return self.value
        elif self.units == "imperial":
            return (self.value - 32) * 5 / 9
        elif self.units == "kelvin":
            return self.value - 273.15
        return self.value
    
    def to_fahrenheit(self) -> float:
        """Convert temperature to Fahrenheit."""
        if self.units == "imperial":
            return self.value
        elif self.units == "metric":
            return self.value * 9 / 5 + 32
        elif self.units == "kelvin":
            return (self.value - 273.15) * 9 / 5 + 32
        return self.value
    
    def to_kelvin(self) -> float:
        """Convert temperature to Kelvin."""
        if self.units == "kelvin":
            return self.value
        elif self.units == "metric":
            return self.value + 273.15
        elif self.units == "imperial":
            return (self.value - 32) * 5 / 9 + 273.15
        return self.value
    
    def __str__(self) -> str:
        """String representation with unit symbol."""
        if self.units == "metric":
            return f"{self.value:.1f}°C"
        elif self.units == "imperial":
            return f"{self.value:.1f}°F"
        elif self.units == "kelvin":
            return f"{self.value:.2f}K"
        return str(self.value)
    
    def __eq__(self, other) -> bool:
        """Equality comparison (compare in same units)."""
        if not isinstance(other, Temperature):
            return False
        # Convert both to Kelvin for comparison
        return abs(self.to_kelvin() - other.to_kelvin()) < 0.01



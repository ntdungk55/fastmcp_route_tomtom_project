from dataclasses import dataclass
from app.domain.errors import DomainError


class InvalidPressureError(DomainError):
    """Raised when pressure value is invalid."""
    pass


@dataclass(frozen=True)
class Pressure:
    """Value object for atmospheric pressure with validation."""
    value: int  # Pressure in hPa/millibars
    
    def __post_init__(self) -> None:
        """Validate pressure value."""
        if not isinstance(self.value, int):
            # Allow float for precision but store as int
            try:
                value_int = int(self.value)
                object.__setattr__(self, 'value', value_int)
            except (ValueError, TypeError):
                raise InvalidPressureError(
                    f"Pressure must be a number, got {type(self.value)}",
                    entity_id="pressure",
                    field="value",
                    value=self.value
                )
        
        # Normal atmospheric pressure range: 870-1085 hPa
        # Extreme but valid ranges for weather data
        if not (800 <= self.value <= 1200):
            raise InvalidPressureError(
                f"Pressure must be between 800 and 1200 hPa, got {self.value}",
                entity_id="pressure",
                field="value",
                value=self.value
            )
    
    def to_inches_mercury(self) -> float:
        """Convert pressure to inches of mercury."""
        return self.value * 0.02952998751
    
    def to_atm(self) -> float:
        """Convert pressure to atmospheres."""
        return self.value / 1013.25
    
    def __str__(self) -> str:
        """String representation."""
        return f"{self.value} hPa"
    
    def __eq__(self, other) -> bool:
        """Equality comparison."""
        if not isinstance(other, Pressure):
            return False
        return self.value == other.value
    
    def __hash__(self) -> int:
        """Hash for use in sets and dicts."""
        return hash(self.value)




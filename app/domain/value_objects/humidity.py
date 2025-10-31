from dataclasses import dataclass
from app.domain.errors import DomainError


class InvalidHumidityError(DomainError):
    """Raised when humidity value is invalid."""
    pass


@dataclass(frozen=True)
class Humidity:
    """Value object for humidity percentage with validation."""
    value: int  # 0-100 percentage
    
    def __post_init__(self) -> None:
        """Validate humidity value."""
        if not isinstance(self.value, int):
            raise InvalidHumidityError(
                f"Humidity must be an integer, got {type(self.value)}",
                entity_id="humidity",
                field="value",
                value=self.value
            )
        
        if not (0 <= self.value <= 100):
            raise InvalidHumidityError(
                f"Humidity must be between 0 and 100, got {self.value}",
                entity_id="humidity",
                field="value",
                value=self.value
            )
    
    def __str__(self) -> str:
        """String representation."""
        return f"{self.value}%"
    
    def __eq__(self, other) -> bool:
        """Equality comparison."""
        if not isinstance(other, Humidity):
            return False
        return self.value == other.value
    
    def __hash__(self) -> int:
        """Hash for use in sets and dicts."""
        return hash(self.value)




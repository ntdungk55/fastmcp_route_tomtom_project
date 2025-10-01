from dataclasses import dataclass
from app.domain.errors import EmptyNameError


@dataclass(frozen=True)
class DestinationName:
    """Value object for destination name with validation"""
    value: str
    
    def __post_init__(self) -> None:
        """Validate destination name"""
        if not self.value:
            raise EmptyNameError(
                "Destination name cannot be None",
                entity_id="destination_name",
                field="value",
                value=self.value
            )
        
        name_trimmed = self.value.strip()
        if not name_trimmed:
            raise EmptyNameError(
                "Destination name cannot be empty or whitespace only",
                entity_id="destination_name",
                field="value",
                value=self.value
            )
        
        if len(name_trimmed) < 2:
            raise EmptyNameError(
                "Destination name must be at least 2 characters long",
                entity_id="destination_name",
                field="value",
                value=self.value
            )
        
        if len(name_trimmed) > 100:
            raise EmptyNameError(
                "Destination name cannot exceed 100 characters",
                entity_id="destination_name",
                field="value",
                value=self.value
            )
        
        # Update the value with trimmed version
        object.__setattr__(self, 'value', name_trimmed)
    
    def __str__(self) -> str:
        """String representation"""
        return self.value
    
    def __eq__(self, other) -> bool:
        """Equality comparison"""
        if not isinstance(other, DestinationName):
            return False
        return self.value == other.value
    
    def __hash__(self) -> int:
        """Hash for use in sets and dicts"""
        return hash(self.value)

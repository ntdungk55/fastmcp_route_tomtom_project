from dataclasses import dataclass
from app.domain.errors import EmptyAddressError


@dataclass(frozen=True)
class Address:
    """Value object for address with validation"""
    value: str
    
    def __post_init__(self) -> None:
        """Validate address"""
        if not self.value:
            raise EmptyAddressError(
                "Destination address cannot be None",
                entity_id="address",
                field="value",
                value=self.value
            )
        
        address_trimmed = self.value.strip()
        if not address_trimmed:
            raise EmptyAddressError(
                "Destination address cannot be empty or whitespace only",
                entity_id="address",
                field="value",
                value=self.value
            )
        
        if len(address_trimmed) < 5:
            raise EmptyAddressError(
                "Destination address must be at least 5 characters long",
                entity_id="address",
                field="value",
                value=self.value
            )
        
        if len(address_trimmed) > 500:
            raise EmptyAddressError(
                "Destination address cannot exceed 500 characters",
                entity_id="address",
                field="value",
                value=self.value
            )
        
        # Update the value with trimmed version
        object.__setattr__(self, 'value', address_trimmed)
    
    def __str__(self) -> str:
        """String representation"""
        return self.value
    
    def __eq__(self, other) -> bool:
        """Equality comparison"""
        if not isinstance(other, Address):
            return False
        return self.value == other.value
    
    def __hash__(self) -> int:
        """Hash for use in sets and dicts"""
        return hash(self.value)

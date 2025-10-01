from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict


class DomainEvent(ABC):
    """Base class for domain events"""
    
    def __init__(self, entity_id: str, event_type: str, data: Dict[str, Any]):
        self.entity_id = entity_id
        self.event_type = event_type
        self.data = data
        self.timestamp = datetime.now()
    
    @abstractmethod
    def get_message(self) -> str:
        """Get human-readable message for this event"""
        pass


class ValidationFailedEvent(DomainEvent):
    """Event raised when domain validation fails"""
    
    def __init__(self, entity_id: str, field: str, value: Any, error_message: str):
        super().__init__(
            entity_id=entity_id,
            event_type="validation_failed",
            data={
                "field": field,
                "value": str(value),
                "error_message": error_message
            }
        )
        self.field = field
        self.value = value
        self.error_message = error_message
    
    def get_message(self) -> str:
        return f"Validation failed for {self.field}: {self.error_message}"


class EntityCreatedEvent(DomainEvent):
    """Event raised when entity is created"""
    
    def __init__(self, entity_id: str, entity_type: str):
        super().__init__(
            entity_id=entity_id,
            event_type="entity_created",
            data={"entity_type": entity_type}
        )
        self.entity_type = entity_type
    
    def get_message(self) -> str:
        return f"Entity {self.entity_type} created with ID: {self.entity_id}"


class EntityUpdatedEvent(DomainEvent):
    """Event raised when entity is updated"""
    
    def __init__(self, entity_id: str, entity_type: str, updated_fields: list):
        super().__init__(
            entity_id=entity_id,
            event_type="entity_updated",
            data={
                "entity_type": entity_type,
                "updated_fields": updated_fields
            }
        )
        self.entity_type = entity_type
        self.updated_fields = updated_fields
    
    def get_message(self) -> str:
        return f"Entity {self.entity_type} updated. Fields: {', '.join(self.updated_fields)}"


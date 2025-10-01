from typing import List, Callable
from app.domain.events.domain_event import DomainEvent
from app.infrastructure.logging.logger import get_logger


class DomainEventHandler:
    """Handler for domain events with unified logging"""
    
    def __init__(self):
        self.logger = get_logger(
            name="domain_events",
            layer="domain",
            component="events"
        )
        self._handlers: List[Callable[[DomainEvent], None]] = []
    
    def register_handler(self, handler: Callable[[DomainEvent], None]):
        """Register an event handler"""
        self._handlers.append(handler)
    
    def handle_event(self, event: DomainEvent):
        """Handle a domain event"""
        # Log the event with context
        self.logger.info(
            f"Domain Event: {event.event_type} - {event.get_message()}",
            extra_context={
                "event_type": event.event_type,
                "entity_id": event.entity_id,
                "timestamp": event.timestamp.isoformat()
            }
        )
        
        # Call all registered handlers
        for handler in self._handlers:
            try:
                handler(event)
            except Exception as e:
                self.logger.error(
                    f"Error in event handler: {e}",
                    extra_context={
                        "event_type": event.event_type,
                        "entity_id": event.entity_id
                    }
                )


# Global event handler instance
_domain_event_handler = DomainEventHandler()


def get_domain_event_handler() -> DomainEventHandler:
    """Get the global domain event handler"""
    return _domain_event_handler


def raise_domain_event(event: DomainEvent):
    """Raise a domain event"""
    _domain_event_handler.handle_event(event)


from typing import Any


class DomainError(Exception):
    """Base for domain-related errors."""
    
    def __init__(self, message: str, entity_id: str = None, field: str = None, value: Any = None):
        super().__init__(message)
        self.message = message
        self.entity_id = entity_id
        self.field = field
        self.value = value
        
        # Log the error using unified logger
        self._log_error()
    
    def _log_error(self):
        """Log the domain error using unified logger"""
        try:
            from app.infrastructure.logging.logger import get_logger
            
            logger = get_logger(
                name="domain_errors",
                layer="domain",
                component="validation",
                entity_id=self.entity_id,
                field=self.field,
                error_type=self.__class__.__name__
            )
            
            logger.error(
                f"Domain validation failed: {self.message}",
                extra_context={
                    "field": self.field,
                    "value": str(self.value) if self.value is not None else None,
                    "error_type": self.__class__.__name__
                }
            )
            
        except ImportError:
            # Fallback logging if unified logger not available
            import logging
            logger = logging.getLogger("domain_errors")
            logger.error(f"Domain Error: {self.message} (Entity: {self.entity_id}, Field: {self.field})")


class InvalidCoordinateError(DomainError):
    """Raised when coordinates are invalid."""
    
    def __init__(self, message: str, entity_id: str = None, field: str = None, value: Any = None):
        super().__init__(message, entity_id, field, value)


class InvalidTravelModeError(DomainError):
    """Raised when travel mode is invalid."""
    
    def __init__(self, message: str, entity_id: str = None, field: str = None, value: Any = None):
        super().__init__(message, entity_id, field, value)


class InvalidDestinationError(DomainError):
    """Raised when destination data is invalid."""
    
    def __init__(self, message: str, entity_id: str = None, field: str = None, value: Any = None):
        super().__init__(message, entity_id, field, value)


class EmptyNameError(InvalidDestinationError):
    """Raised when destination name is empty or invalid."""
    
    def __init__(self, message: str, entity_id: str = None, field: str = "name", value: Any = None):
        super().__init__(message, entity_id, field, value)


class EmptyAddressError(InvalidDestinationError):
    """Raised when destination address is empty or invalid."""
    
    def __init__(self, message: str, entity_id: str = None, field: str = "address", value: Any = None):
        super().__init__(message, entity_id, field, value)


class InvalidDateTimeError(DomainError):
    """Raised when datetime values are invalid."""
    
    def __init__(self, message: str, entity_id: str = None, field: str = None, value: Any = None):
        super().__init__(message, entity_id, field, value)


# Weather domain errors (imported from value objects)
from app.domain.value_objects.temperature import InvalidTemperatureError
from app.domain.value_objects.weather_description import InvalidWeatherDescriptionError
from app.domain.value_objects.weather_units import InvalidWeatherUnitsError
from app.domain.value_objects.humidity import InvalidHumidityError
from app.domain.value_objects.pressure import InvalidPressureError
from app.domain.value_objects.wind_speed import InvalidWindSpeedError
from app.domain.value_objects.location_name import InvalidLocationNameError
# Note: InvalidWeatherDataError is defined in app.domain.entities.weather
# Import it directly from there if needed to avoid circular imports
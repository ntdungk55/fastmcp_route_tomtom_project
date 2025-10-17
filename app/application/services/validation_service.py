"""Validation service for common validation operations."""

from typing import Union
from app.domain.value_objects.latlon import LatLon
from app.infrastructure.logging.logger import get_logger

logger = get_logger(__name__)


class ValidationService:
    """Service for common validation operations."""
    
    @staticmethod
    def safe_float_convert(value: Union[str, float, int]) -> float:
        """Safely convert value to float."""
        try:
            return float(value)
        except (ValueError, TypeError) as e:
            logger.error(f"Failed to convert {value} to float: {str(e)}")
            raise ValueError(f"Cannot convert {value} to float")
    
    @staticmethod
    def validate_coordinates(lat: Union[str, float], lon: Union[str, float]) -> LatLon:
        """Validate and convert latitude/longitude to LatLon value object."""
        try:
            lat_float = ValidationService.safe_float_convert(lat)
            lon_float = ValidationService.safe_float_convert(lon)
            return LatLon(lat_float, lon_float)
        except Exception as e:
            logger.error(f"Invalid coordinates: lat={lat}, lon={lon}, error={str(e)}")
            raise ValueError(f"Invalid coordinates: {str(e)}")


def get_validation_service() -> ValidationService:
    """Factory function to get validation service instance."""
    return ValidationService()

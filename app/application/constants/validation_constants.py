"""
Validation constants cho Application layer.
"""
from typing import Dict, List


class ValidationMessages:
    """Validation error messages."""
    # Coordinate validation
    INVALID_LATITUDE = "Invalid latitude: {value}. Must be between -90 and 90"
    INVALID_LONGITUDE = "Invalid longitude: {value}. Must be between -180 and 180"
    INVALID_COORDINATES = "Invalid coordinates: lat={lat}, lon={lon}"
    
    # String validation
    EMPTY_FIELD = "{field_name} cannot be empty"
    INVALID_FORMAT = "Invalid format for {field_name}: {value}"
    
    # Numeric validation
    INVALID_NUMBER = "Cannot convert '{value}' to {number_type}: {error}"
    OUT_OF_RANGE = "{field_name} must be between {min_val} and {max_val}, got {value}"
    
    # Enum validation
    INVALID_ENUM_VALUE = "Invalid {enum_name}: {value}. Valid values: {valid_values}"
    
    # API validation
    MISSING_API_KEY = "API key is required"
    INVALID_API_KEY = "Invalid API key format"
    
    # Request validation
    MISSING_FIELD = "Missing required field: {field_name}"
    INVALID_REQUEST_FORMAT = "Invalid request format: {error}"


class ValidationLimits:
    """Validation limits."""
    # String lengths
    MAX_ADDRESS_LENGTH = 1000
    MAX_QUERY_LENGTH = 500
    MIN_ADDRESS_LENGTH = 3
    
    # Numeric ranges
    MAX_ZOOM_LEVEL = 22
    MIN_ZOOM_LEVEL = 0
    
    MAX_LIMIT_VALUE = 100
    MIN_LIMIT_VALUE = 1
    
    # Coordinate precision
    COORDINATE_PRECISION = 6  # decimal places
    
    # Timeout limits
    MAX_TIMEOUT_SECONDS = 300
    MIN_TIMEOUT_SECONDS = 1


class ValidationPatterns:
    """Regex patterns cho validation."""
    # Coordinate patterns
    LATITUDE_PATTERN = r"^-?([0-8]?[0-9](\.[0-9]+)?|90(\.0+)?)$"
    LONGITUDE_PATTERN = r"^-?(1[0-7][0-9](\.[0-9]+)?|[0-9]?[0-9](\.[0-9]+)?|180(\.0+)?)$"
    
    # Address patterns
    ADDRESS_PATTERN = r"^[a-zA-Z0-9\s,.-/àáảãạăắằẳẵặâấầẩẫậđèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵ]+$"
    
    # API key pattern (example for TomTom)
    API_KEY_PATTERN = r"^[a-zA-Z0-9]{32}$"
    
    # Language code pattern
    LANGUAGE_CODE_PATTERN = r"^[a-z]{2}-[A-Z]{2}$"
    
    # Country code pattern  
    COUNTRY_CODE_PATTERN = r"^[A-Z]{2}$"


class DefaultValues:
    """Default values cho validation - sử dụng constants từ Domain layer."""
    # Import constants from Domain layer để tránh duplicate
    from app.domain.constants.api_constants import LanguageConstants, CountryConstants, TravelModeConstants
    
    DEFAULT_LANGUAGE = LanguageConstants.DEFAULT
    DEFAULT_COUNTRY = CountryConstants.DEFAULT
    DEFAULT_LIMIT = 1
    DEFAULT_ZOOM = 10
    DEFAULT_TIMEOUT = 30
    DEFAULT_MAX_ALTERNATIVES = 1
    DEFAULT_TRAVEL_MODE = TravelModeConstants.CAR
    # Import constants from Domain layer
    from app.domain.constants.api_constants import RouteTypeConstants
    DEFAULT_ROUTE_TYPE = RouteTypeConstants.FASTEST

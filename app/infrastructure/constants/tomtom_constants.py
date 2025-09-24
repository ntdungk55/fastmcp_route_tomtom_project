"""
TomTom API specific constants.
Thuộc Infrastructure layer - external service constants.
"""
from typing import Dict, Optional


class TomTomEndpoints:
    """TomTom API endpoints."""
    # Base URLs
    BASE_URL = "https://api.tomtom.com"
    
    # Routing API
    ROUTING_BASE = "/routing/1"
    CALCULATE_ROUTE = "/calculateRoute/{origin}/{destination}/json"
    
    # Geocoding API  
    GEOCODING_BASE = "/search/2"
    GEOCODE = "/geocode/{query}.json"
    STRUCTURED_GEOCODE = "/structuredGeocode.json"
    
    # Traffic API
    TRAFFIC_BASE = "/traffic"
    TRAFFIC_FLOW = "/services/4/flowSegmentData"
    TRAFFIC_INCIDENTS = "/services/5/incidentDetails"
    
    @classmethod
    def get_full_routing_url(cls, base_url: Optional[str] = None) -> str:
        """Lấy full routing URL."""
        base = base_url or cls.BASE_URL
        return f"{base}{cls.ROUTING_BASE}"
    
    @classmethod
    def get_full_geocoding_url(cls, base_url: Optional[str] = None) -> str:
        """Lấy full geocoding URL."""
        base = base_url or cls.BASE_URL
        return f"{base}{cls.GEOCODING_BASE}"
    
    @classmethod
    def get_full_traffic_url(cls, base_url: Optional[str] = None) -> str:
        """Lấy full traffic URL."""
        base = base_url or cls.BASE_URL
        return f"{base}{cls.TRAFFIC_BASE}"


class TomTomDefaults:
    """TomTom API default values."""
    # Timeout settings
    DEFAULT_TIMEOUT_SEC = 30
    MAX_TIMEOUT_SEC = 120
    MIN_TIMEOUT_SEC = 5
    
    # Retry settings
    MAX_RETRIES = 3
    RETRY_DELAY_SEC = 1
    BACKOFF_FACTOR = 2
    
    # Rate limiting
    REQUESTS_PER_SECOND = 50
    BURST_LIMIT = 100
    
    # Response format
    RESPONSE_FORMAT = "json"
    API_VERSION = "1"
    
    # Default query parameters
    DEFAULT_UNIT_SYSTEM = "metric"
    DEFAULT_INSTRUCTION_TYPE = "text"
    DEFAULT_SECTION_TYPE = "traffic"


class TomTomErrorCodes:
    """TomTom API error codes và messages."""
    # HTTP Status codes
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    TOO_MANY_REQUESTS = 429
    INTERNAL_SERVER_ERROR = 500
    SERVICE_UNAVAILABLE = 503
    
    # Custom error messages
    ERROR_MESSAGES = {
        BAD_REQUEST: "Invalid request parameters",
        UNAUTHORIZED: "Invalid API key",
        FORBIDDEN: "Access denied", 
        NOT_FOUND: "Resource not found",
        TOO_MANY_REQUESTS: "Rate limit exceeded",
        INTERNAL_SERVER_ERROR: "TomTom server error",
        SERVICE_UNAVAILABLE: "TomTom service unavailable"
    }
    
    @classmethod
    def get_error_message(cls, status_code: int) -> str:
        """Lấy error message cho status code."""
        return cls.ERROR_MESSAGES.get(status_code, f"Unknown error: {status_code}")


class TomTomHeaders:
    """TomTom API headers."""
    USER_AGENT = "TomTom-MCP-Server/1.0"
    ACCEPT = "application/json"
    CONTENT_TYPE = "application/json"
    
    @classmethod
    def get_default_headers(cls) -> Dict[str, str]:
        """Lấy default headers."""
        return {
            "User-Agent": cls.USER_AGENT,
            "Accept": cls.ACCEPT,
            "Content-Type": cls.CONTENT_TYPE
        }

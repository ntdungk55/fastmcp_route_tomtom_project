"""Infrastructure layer dependencies provider."""

from typing import Dict, Any
from app.infrastructure.config.settings import Settings
from app.infrastructure.http.client import AsyncApiClient
from app.infrastructure.logging.logger import get_logger
from app.infrastructure.adapters.memory_destination_repository import MemoryDestinationRepository
from app.infrastructure.tomtom.adapters.geocoding_adapter import TomTomGeocodingAdapter
from app.infrastructure.tomtom.adapters.routing_adapter import TomTomRoutingAdapter
from app.infrastructure.tomtom.adapters.traffic_adapter import TomTomTrafficAdapter
from app.infrastructure.config.api_config import get_config_service


class InfrastructureProvider:
    """Provider for infrastructure layer dependencies."""
    
    def __init__(self, settings: Settings):
        """Initialize infrastructure provider with settings."""
        self._settings = settings
        self._http_client = None
        self._adapters = {}
        self._repositories = {}
        self._services = {}
    
    def get_http_client(self) -> AsyncApiClient:
        """Get HTTP client (singleton)."""
        if self._http_client is None:
            self._http_client = AsyncApiClient()
        return self._http_client
    
    def get_adapters(self) -> Dict[str, Any]:
        """Get all adapters."""
        if not self._adapters:
            base_config = {
                "base_url": self._settings.tomtom_base_url,
                "api_key": self._settings.tomtom_api_key,
                "http": self.get_http_client(),
                "timeout_sec": self._settings.http_timeout_sec,
            }
            
            self._adapters = {
                "routing_adapter": TomTomRoutingAdapter(**base_config),
                "geocoding_adapter": TomTomGeocodingAdapter(**base_config),
                "traffic_adapter": TomTomTrafficAdapter(**base_config)
            }
        
        return self._adapters
    
    def get_repositories(self) -> Dict[str, Any]:
        """Get all repositories."""
        if not self._repositories:
            self._repositories = {
                "destination_repository": MemoryDestinationRepository()
            }
        
        return self._repositories
    
    def get_services(self) -> Dict[str, Any]:
        """Get infrastructure services."""
        if not self._services:
            self._services = {
                "config_service": get_config_service(),
                "logger": get_logger("infrastructure")
            }
        
        return self._services
    
    def get_all_dependencies(self) -> Dict[str, Any]:
        """Get all infrastructure dependencies."""
        return {
            **self.get_adapters(),
            **self.get_repositories(),
            **self.get_services(),
            "http_client": self.get_http_client(),
            "settings": self._settings
        }

"""Gateway factory patterns."""

from typing import Dict, Any, Type, Protocol
from app.infrastructure.http.client import AsyncApiClient
from app.infrastructure.tomtom.adapters.geocoding_adapter import TomTomGeocodingAdapter
from app.infrastructure.tomtom.adapters.routing_adapter import TomTomRoutingAdapter
from app.infrastructure.tomtom.adapters.traffic_adapter import TomTomTrafficAdapter
from app.infrastructure.config.settings import Settings


class GatewayFactory(Protocol):
    """Gateway factory protocol."""
    
    def create_http_client(self) -> AsyncApiClient:
        """Create HTTP client."""
        ...
    
    def create_geocoding_adapter(self, settings: Settings) -> Any:
        """Create geocoding adapter."""
        ...
    
    def create_routing_adapter(self, settings: Settings) -> Any:
        """Create routing adapter."""
        ...
    
    def create_traffic_adapter(self, settings: Settings) -> Any:
        """Create traffic adapter."""
        ...


class TomTomGatewayFactory:
    """TomTom gateway factory."""
    
    def __init__(self):
        """Initialize TomTom gateway factory."""
        self._gateways: Dict[str, Any] = {}
    
    def create_http_client(self) -> AsyncApiClient:
        """Create HTTP client."""
        if "http_client" not in self._gateways:
            self._gateways["http_client"] = AsyncApiClient()
        return self._gateways["http_client"]
    
    def create_geocoding_adapter(self, settings: Settings) -> TomTomGeocodingAdapter:
        """Create geocoding adapter."""
        key = "geocoding_adapter"
        if key not in self._gateways:
            base_config = {
                "base_url": settings.tomtom_base_url,
                "api_key": settings.tomtom_api_key,
                "http": self.create_http_client(),
                "timeout_sec": settings.http_timeout_sec,
            }
            self._gateways[key] = TomTomGeocodingAdapter(**base_config)
        return self._gateways[key]
    
    def create_routing_adapter(self, settings: Settings) -> TomTomRoutingAdapter:
        """Create routing adapter."""
        key = "routing_adapter"
        if key not in self._gateways:
            base_config = {
                "base_url": settings.tomtom_base_url,
                "api_key": settings.tomtom_api_key,
                "http": self.create_http_client(),
                "timeout_sec": settings.http_timeout_sec,
            }
            self._gateways[key] = TomTomRoutingAdapter(**base_config)
        return self._gateways[key]
    
    def create_traffic_adapter(self, settings: Settings) -> TomTomTrafficAdapter:
        """Create traffic adapter."""
        key = "traffic_adapter"
        if key not in self._gateways:
            base_config = {
                "base_url": settings.tomtom_base_url,
                "api_key": settings.tomtom_api_key,
                "http": self.create_http_client(),
                "timeout_sec": settings.http_timeout_sec,
            }
            self._gateways[key] = TomTomTrafficAdapter(**base_config)
        return self._gateways[key]
    
    def get_all_adapters(self, settings: Settings) -> Dict[str, Any]:
        """Get all adapters."""
        return {
            "geocoding_adapter": self.create_geocoding_adapter(settings),
            "routing_adapter": self.create_routing_adapter(settings),
            "traffic_adapter": self.create_traffic_adapter(settings),
            "http_client": self.create_http_client()
        }


class GatewayFactoryManager:
    """Gateway factory manager."""
    
    def __init__(self):
        """Initialize gateway factory manager."""
        self._factory = TomTomGatewayFactory()
    
    def get_factory(self) -> TomTomGatewayFactory:
        """Get gateway factory."""
        return self._factory
    
    def create_all_adapters(self, settings: Settings) -> Dict[str, Any]:
        """Create all adapters."""
        return self._factory.get_all_adapters(settings)

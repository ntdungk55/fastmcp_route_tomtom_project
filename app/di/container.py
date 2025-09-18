"""Dependency Injection Container - Wire tất cả dependencies."""

# Use Cases
from app.application.use_cases.analyze_route_traffic import AnalyzeRouteTraffic
from app.application.use_cases.calculate_route import CalculateRoute
from app.application.use_cases.check_address_traffic import CheckAddressTraffic
from app.application.use_cases.geocode_address import GeocodeAddress
from app.application.use_cases.get_intersection_position import GetIntersectionPosition
from app.application.use_cases.get_street_center import GetStreetCenter
from app.application.use_cases.get_traffic_condition import GetTrafficCondition

# Infrastructure
from app.infrastructure.config.settings import Settings
from app.infrastructure.http.client import AsyncApiClient
from app.infrastructure.logging.logger import get_logger
from app.infrastructure.tomtom.adapters.geocoding_adapter import TomTomGeocodingAdapter
from app.infrastructure.tomtom.adapters.routing_adapter import TomTomRoutingAdapter
from app.infrastructure.tomtom.adapters.traffic_adapter import TomTomTrafficAdapter


class Container:
    """DI Container quản lý tất cả dependencies theo Clean Architecture.
    
    Chức năng: Wire các Use Cases với Adapters và cung cấp dependencies
    Kiến trúc: Dependency Injection pattern với lazy initialization
    """
    
    def __init__(self, settings: Settings | None = None):
        """Khởi tạo container với settings."""
        self.logger = get_logger("container")
        self.settings = settings or Settings()
        self.settings.validate()

        # Infrastructure layer - HTTP client
        self.http = AsyncApiClient()
        
        # Infrastructure layer - TomTom Adapters
        self._init_adapters()
        
        # Application layer - Use Cases
        self._init_use_cases()
    
    def _init_adapters(self):
        """Khởi tạo tất cả TomTom adapters."""
        base_config = {
            "base_url": self.settings.tomtom_base_url,
            "api_key": self.settings.tomtom_api_key,
            "http": self.http,
            "timeout_sec": self.settings.http_timeout_sec,
        }
        
        # Routing adapter (đã có sẵn)
        self.routing_adapter = TomTomRoutingAdapter(**base_config)
        
        # Geocoding adapter (mới)
        self.geocoding_adapter = TomTomGeocodingAdapter(**base_config)
        
        # Traffic adapter (mới)
        self.traffic_adapter = TomTomTrafficAdapter(**base_config)
    
    def _init_use_cases(self):
        """Khởi tạo tất cả Use Cases với dependency injection."""
        
        # Routing Use Cases
        self.calculate_route = CalculateRoute(self.routing_adapter)
        
        # Geocoding Use Cases
        self.geocode_address = GeocodeAddress(self.geocoding_adapter)
        self.get_intersection_position = GetIntersectionPosition(self.geocoding_adapter)
        self.get_street_center = GetStreetCenter(self.geocoding_adapter)
        
        # Traffic Use Cases
        self.get_traffic_condition = GetTrafficCondition(self.traffic_adapter)
        self.analyze_route_traffic = AnalyzeRouteTraffic(self.traffic_adapter)
        
        # Composite Use Cases (cần nhiều adapters)
        self.check_address_traffic = CheckAddressTraffic(
            geocoding=self.geocoding_adapter,
            traffic=self.traffic_adapter
        )
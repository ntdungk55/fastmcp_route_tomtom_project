"""Application layer dependencies provider."""

from typing import Dict, Any
from app.application.ports.destination_repository import DestinationRepository
from app.application.ports.geocoding_provider import GeocodingProvider
from app.application.ports.routing_provider import RoutingProvider
from app.application.ports.traffic_provider import TrafficProvider
from app.application.use_cases.save_destination import SaveDestinationUseCase
from app.application.use_cases.calculate_route import CalculateRoute
from app.application.use_cases.geocode_address import GeocodeAddress
from app.application.use_cases.get_intersection_position import GetIntersectionPosition
from app.application.use_cases.get_street_center import GetStreetCenter
from app.application.use_cases.get_traffic_condition import GetTrafficCondition
from app.application.use_cases.analyze_route_traffic import AnalyzeRouteTraffic
from app.application.use_cases.check_address_traffic import CheckAddressTraffic
from app.application.services.validation_service import get_validation_service
from app.application.services.request_handler import get_request_handler_service


class ApplicationProvider:
    """Provider for application layer dependencies."""
    
    def __init__(
        self,
        destination_repository: DestinationRepository,
        geocoding_provider: GeocodingProvider,
        routing_provider: RoutingProvider,
        traffic_provider: TrafficProvider
    ):
        """Initialize application provider with dependencies."""
        self._destination_repository = destination_repository
        self._geocoding_provider = geocoding_provider
        self._routing_provider = routing_provider
        self._traffic_provider = traffic_provider
    
    def get_use_cases(self) -> Dict[str, Any]:
        """Get all use cases."""
        return {
            "save_destination": SaveDestinationUseCase(
                destination_repository=self._destination_repository,
                geocoding_provider=self._geocoding_provider
            ),
            "calculate_route": CalculateRoute(self._routing_provider),
            "geocode_address": GeocodeAddress(self._geocoding_provider),
            "get_intersection_position": GetIntersectionPosition(self._geocoding_provider),
            "get_street_center": GetStreetCenter(self._geocoding_provider),
            "get_traffic_condition": GetTrafficCondition(self._traffic_provider),
            "analyze_route_traffic": AnalyzeRouteTraffic(self._traffic_provider),
            "check_address_traffic": CheckAddressTraffic(
                geocoding=self._geocoding_provider,
                traffic=self._traffic_provider
            )
        }
    
    def get_services(self) -> Dict[str, Any]:
        """Get application services."""
        return {
            "validation_service": get_validation_service(),
            "request_handler": get_request_handler_service()
        }
    
    def get_ports(self) -> Dict[str, Any]:
        """Get application ports."""
        return {
            "destination_repository": self._destination_repository,
            "geocoding_provider": self._geocoding_provider,
            "routing_provider": self._routing_provider,
            "traffic_provider": self._traffic_provider
        }

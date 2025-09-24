"""Domain layer dependencies provider."""

from typing import Dict, Any
from app.domain.entities.destination import Destination
from app.domain.value_objects.latlon import LatLon
from app.domain.enums.travel_mode import TravelMode
from app.domain.enums.route_type import RouteType


class DomainProvider:
    """Provider for domain layer dependencies."""
    
    @staticmethod
    def create_latlon(latitude: float, longitude: float) -> LatLon:
        """Create LatLon value object."""
        return LatLon(latitude, longitude)
    
    @staticmethod
    def create_destination(
        name: str,
        address: str,
        coordinates: LatLon,
        destination_id: str | None = None
    ) -> Destination:
        """Create Destination entity."""
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        
        return Destination(
            id=destination_id,
            name=name,
            address=address,
            coordinates=coordinates,
            created_at=now,
            updated_at=now
        )
    
    @staticmethod
    def create_travel_mode(mode: str) -> TravelMode:
        """Create TravelMode enum."""
        return TravelMode(mode)
    
    @staticmethod
    def create_route_type(route_type: str) -> RouteType:
        """Create RouteType enum."""
        return RouteType(route_type)
    
    @staticmethod
    def get_domain_services() -> Dict[str, Any]:
        """Get domain services."""
        return {
            # Domain services sẽ được thêm ở đây khi cần
        }

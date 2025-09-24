"""
Route type enum cho routing preferences.
"""
from enum import Enum
from app.domain.constants.api_constants import RouteTypeConstants


class RouteType(str, Enum):
    """Route type enum với constants từ domain constants."""
    FASTEST = RouteTypeConstants.FASTEST
    SHORTEST = RouteTypeConstants.SHORTEST
    ECO = RouteTypeConstants.ECO
    THRILLING = RouteTypeConstants.THRILLING
    
    @classmethod
    def from_string(cls, value: str) -> 'RouteType':
        """Tạo RouteType từ string value."""
        for route_type in cls:
            if route_type.value == value:
                return route_type
        raise ValueError(f"Invalid route type: {value}")
    
    @classmethod
    def get_all_values(cls) -> list[str]:
        """Lấy tất cả route type values."""
        return [route_type.value for route_type in cls]
    
    @property
    def is_fastest(self) -> bool:
        """Kiểm tra có phải fastest route không."""
        return self == self.FASTEST
    
    @property
    def is_eco_friendly(self) -> bool:
        """Kiểm tra có phải eco-friendly route không."""
        return self == self.ECO



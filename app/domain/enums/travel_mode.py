
from enum import Enum
from app.domain.constants.api_constants import TravelModeConstants


class TravelMode(str, Enum):
    """Travel mode enum với constants từ domain constants."""
    CAR = TravelModeConstants.CAR
    BICYCLE = TravelModeConstants.BICYCLE
    FOOT = TravelModeConstants.FOOT
    MOTORCYCLE = TravelModeConstants.MOTORCYCLE
    
    @classmethod
    def get_tomtom_value(cls, mode: 'TravelMode') -> str:
        """Convert travel mode sang TomTom API value."""
        return TravelModeConstants.get_tomtom_value(mode.value)
    
    @classmethod
    def from_string(cls, value: str) -> 'TravelMode':
        """Tạo TravelMode từ string value."""
        for mode in cls:
            if mode.value == value:
                return mode
        raise ValueError(f"Invalid travel mode: {value}")
    
    @classmethod
    def get_all_values(cls) -> list[str]:
        """Lấy tất cả travel mode values."""
        return [mode.value for mode in cls]

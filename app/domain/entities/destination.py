from dataclasses import dataclass
from typing import Optional
from datetime import datetime
from app.domain.value_objects.latlon import LatLon


@dataclass
class Destination:
    """Entity representing a saved destination"""
    id: Optional[str]
    name: str
    address: str
    coordinates: LatLon
    created_at: datetime
    updated_at: datetime
    
    def __post_init__(self):
        """Validate entity after initialization"""
        if not self.name or not self.name.strip():
            raise ValueError("Destination name cannot be empty")
        if not self.address or not self.address.strip():
            raise ValueError("Destination address cannot be empty")
        if not isinstance(self.coordinates, LatLon):
            raise ValueError("Coordinates must be a LatLon value object")

from dataclasses import dataclass
from typing import Optional
from app.domain.value_objects.latlon import LatLon


@dataclass
class SaveDestinationRequest:
    """DTO for save destination request"""
    name: Optional[str]
    address: str


@dataclass
class SaveDestinationResponse:
    """DTO for save destination response"""
    success: bool
    destination_id: Optional[str] = None
    message: Optional[str] = None
    error: Optional[str] = None

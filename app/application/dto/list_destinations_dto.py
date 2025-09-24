from dataclasses import dataclass
from typing import List, Optional
from app.domain.entities.destination import Destination


@dataclass
class ListDestinationsRequest:
    """DTO for list destinations request."""
    pass  # No parameters needed for listing all


@dataclass
class DestinationSummary:
    """DTO for destination summary in list."""
    id: str
    name: str
    address: str
    latitude: float
    longitude: float
    created_at: str
    updated_at: str


@dataclass
class ListDestinationsResponse:
    """DTO for list destinations response."""
    success: bool
    destinations: List[DestinationSummary]
    total_count: int
    message: Optional[str] = None
    error: Optional[str] = None

from dataclasses import dataclass
from typing import Optional, List


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
class SearchDestinationsRequest:
    """DTO for search destinations request."""
    id: Optional[str] = None
    name: Optional[str] = None
    address: Optional[str] = None


@dataclass
class SearchDestinationsResponse:
    """DTO for search destinations response."""
    success: bool
    destinations: List[DestinationSummary]
    total_count: int
    message: Optional[str] = None
    error: Optional[str] = None

from dataclasses import dataclass
from typing import Optional


@dataclass
class UpdateDestinationRequest:
    """DTO for update destination request."""
    destination_id: str
    name: Optional[str] = None
    address: Optional[str] = None


@dataclass
class UpdateDestinationResponse:
    """DTO for update destination response."""
    success: bool
    destination_id: Optional[str] = None
    message: Optional[str] = None
    error: Optional[str] = None

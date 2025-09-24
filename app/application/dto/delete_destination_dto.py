from dataclasses import dataclass
from typing import Optional


@dataclass
class DeleteDestinationRequest:
    """DTO for delete destination request."""
    destination_id: str


@dataclass
class DeleteDestinationResponse:
    """DTO for delete destination response."""
    success: bool
    deleted: bool
    message: Optional[str] = None
    error: Optional[str] = None

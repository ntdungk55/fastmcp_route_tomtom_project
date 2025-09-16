
class DomainError(Exception):
    """Base for domain-related errors."""


class InvalidCoordinateError(DomainError):
    """Raised when coordinates are invalid."""


class InvalidTravelModeError(DomainError):
    """Raised when travel mode is invalid."""


class ApplicationError(Exception):
    """Base for application errors."""


class RoutingProviderError(ApplicationError):
    """Raised when routing provider fails."""


class ValidationError(ApplicationError):
    """Raised when command validation fails."""

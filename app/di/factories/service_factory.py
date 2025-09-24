"""Service factory patterns."""

from typing import Dict, Any, Type, Protocol
from app.application.services.validation_service import get_validation_service
from app.application.services.request_handler import get_request_handler_service
from app.infrastructure.config.api_config import get_config_service
from app.infrastructure.logging.logger import get_logger


class ServiceFactory(Protocol):
    """Service factory protocol."""
    
    def create_validation_service(self) -> Any:
        """Create validation service."""
        ...
    
    def create_request_handler_service(self) -> Any:
        """Create request handler service."""
        ...


class ApplicationServiceFactory:
    """Application service factory."""
    
    def __init__(self):
        """Initialize application service factory."""
        self._services: Dict[str, Any] = {}
    
    def create_validation_service(self) -> Any:
        """Create validation service."""
        if "validation_service" not in self._services:
            self._services["validation_service"] = get_validation_service()
        return self._services["validation_service"]
    
    def create_request_handler_service(self) -> Any:
        """Create request handler service."""
        if "request_handler_service" not in self._services:
            self._services["request_handler_service"] = get_request_handler_service()
        return self._services["request_handler_service"]
    
    def get_all_services(self) -> Dict[str, Any]:
        """Get all application services."""
        return {
            "validation_service": self.create_validation_service(),
            "request_handler_service": self.create_request_handler_service()
        }


class InfrastructureServiceFactory:
    """Infrastructure service factory."""
    
    def __init__(self):
        """Initialize infrastructure service factory."""
        self._services: Dict[str, Any] = {}
    
    def create_config_service(self) -> Any:
        """Create config service."""
        if "config_service" not in self._services:
            self._services["config_service"] = get_config_service()
        return self._services["config_service"]
    
    def create_logger(self, name: str = "infrastructure") -> Any:
        """Create logger."""
        key = f"logger_{name}"
        if key not in self._services:
            self._services[key] = get_logger(name)
        return self._services[key]
    
    def get_all_services(self) -> Dict[str, Any]:
        """Get all infrastructure services."""
        return {
            "config_service": self.create_config_service(),
            "logger": self.create_logger()
        }


class ServiceFactoryManager:
    """Service factory manager."""
    
    def __init__(self):
        """Initialize service factory manager."""
        self._app_factory = ApplicationServiceFactory()
        self._infra_factory = InfrastructureServiceFactory()
    
    def get_application_services(self) -> Dict[str, Any]:
        """Get application services."""
        return self._app_factory.get_all_services()
    
    def get_infrastructure_services(self) -> Dict[str, Any]:
        """Get infrastructure services."""
        return self._infra_factory.get_all_services()
    
    def get_all_services(self) -> Dict[str, Any]:
        """Get all services."""
        return {
            **self.get_application_services(),
            **self.get_infrastructure_services()
        }

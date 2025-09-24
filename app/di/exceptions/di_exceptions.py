"""Dependency injection exceptions."""


class DIContainerError(Exception):
    """Base exception for DI container errors."""
    pass


class DependencyNotFoundError(DIContainerError):
    """Exception raised when dependency is not found."""
    
    def __init__(self, dependency_name: str):
        """Initialize dependency not found error."""
        self.dependency_name = dependency_name
        super().__init__(f"Dependency '{dependency_name}' not found in container")


class CircularDependencyError(DIContainerError):
    """Exception raised when circular dependency is detected."""
    
    def __init__(self, dependency_chain: list):
        """Initialize circular dependency error."""
        self.dependency_chain = dependency_chain
        chain_str = " -> ".join(dependency_chain)
        super().__init__(f"Circular dependency detected: {chain_str}")


class DependencyRegistrationError(DIContainerError):
    """Exception raised when dependency registration fails."""
    
    def __init__(self, dependency_name: str, reason: str):
        """Initialize dependency registration error."""
        self.dependency_name = dependency_name
        self.reason = reason
        super().__init__(f"Failed to register dependency '{dependency_name}': {reason}")


class ScopeError(DIContainerError):
    """Exception raised when scope operation fails."""
    
    def __init__(self, scope_name: str, operation: str, reason: str):
        """Initialize scope error."""
        self.scope_name = scope_name
        self.operation = operation
        self.reason = reason
        super().__init__(f"Scope '{scope_name}' {operation} failed: {reason}")


class FactoryError(DIContainerError):
    """Exception raised when factory operation fails."""
    
    def __init__(self, factory_name: str, reason: str):
        """Initialize factory error."""
        self.factory_name = factory_name
        self.reason = reason
        super().__init__(f"Factory '{factory_name}' failed: {reason}")


class ProviderError(DIContainerError):
    """Exception raised when provider operation fails."""
    
    def __init__(self, provider_name: str, reason: str):
        """Initialize provider error."""
        self.provider_name = provider_name
        self.reason = reason
        super().__init__(f"Provider '{provider_name}' failed: {reason}")

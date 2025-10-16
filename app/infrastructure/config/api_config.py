"""
Configuration service cho API settings và keys.
Thuộc Infrastructure layer - xử lý external configuration.
"""
import os
from typing import Optional
from dataclasses import dataclass
from app.interfaces.constants.mcp_constants import MCPServerConstants

@dataclass(frozen=True)
class ApiConfig:
    """Configuration cho API keys và settings."""
    tomtom_api_key: str
    server_host: str = MCPServerConstants.DEFAULT_HOST
    server_port: int = MCPServerConstants.DEFAULT_PORT
    
    @classmethod
    def from_environment(cls) -> "ApiConfig":
        """Tạo config từ environment variables."""
        api_key = os.getenv("TOMTOM_API_KEY")
        if not api_key:
            raise ValueError("TOMTOM_API_KEY environment variable is required!")
        
        return cls(
            tomtom_api_key=api_key,
            server_host=os.getenv("SERVER_HOST", MCPServerConstants.DEFAULT_HOST),
            server_port=int(os.getenv("SERVER_PORT", MCPServerConstants.DEFAULT_PORT))
        )

class ConfigService:
    """Service để quản lý configuration."""
    
    def __init__(self):
        self._config: Optional[ApiConfig] = None
    
    def get_config(self) -> ApiConfig:
        """Lấy configuration, lazy load nếu chưa có."""
        if self._config is None:
            self._config = ApiConfig.from_environment()
        return self._config
    
    def reload_config(self) -> ApiConfig:
        """Reload configuration từ environment."""
        self._config = ApiConfig.from_environment()
        return self._config

# Singleton instance
_config_service = ConfigService()

def get_config_service() -> ConfigService:
    """Factory function để lấy config service."""
    return _config_service



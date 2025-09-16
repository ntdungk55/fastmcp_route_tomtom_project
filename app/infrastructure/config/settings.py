
import os
from typing import Optional
from pydantic import BaseModel, Field, validator


class Settings(BaseModel):
    tomtom_base_url: str = Field(
        default_factory=lambda: os.getenv("TOMTOM_BASE_URL", "https://api.tomtom.com")
    )
    tomtom_api_key: str = Field(
        default_factory=lambda: os.getenv("TOMTOM_API_KEY", "")
    )
    http_timeout_sec: int = Field(
        default_factory=lambda: int(os.getenv("HTTP_TIMEOUT_SEC", "12")),
        ge=1, le=300
    )
    log_level: str = Field(
        default_factory=lambda: os.getenv("LOG_LEVEL", "INFO")
    )

    @validator('tomtom_base_url')
    def validate_url(cls, v: str) -> str:
        if not v.startswith(('http://', 'https://')):
            raise ValueError('Base URL must start with http:// or https://')
        return v.rstrip('/')

    @validator('tomtom_api_key')
    def validate_api_key(cls, v: str) -> str:
        if not v:
            raise ValueError("TOMTOM_API_KEY is required")
        return v

    @validator('log_level')
    def validate_log_level(cls, v: str) -> str:
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of: {valid_levels}")
        return v.upper()

    def validate(self) -> None:
        """Legacy method for backward compatibility."""
        pass  # Pydantic handles validation automatically

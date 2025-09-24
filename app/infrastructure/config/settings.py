
import os

from pydantic import BaseModel, Field, field_validator


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
    database_path: str = Field(
        default_factory=lambda: os.getenv("DATABASE_PATH", "app/infrastructure/persistence/database/destinations.db")
    )

    @field_validator('tomtom_base_url')
    @classmethod
    def validate_url(cls, v: str) -> str:
        if not v.startswith(('http://', 'https://')):
            raise ValueError('Base URL must start with http:// or https://')
        return v.rstrip('/')

    @field_validator('tomtom_api_key')
    @classmethod
    def validate_api_key(cls, v: str) -> str:
        if not v:
            raise ValueError("TOMTOM_API_KEY is required")
        return v

    @field_validator('log_level')
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of: {valid_levels}")
        return v.upper()

    def validate(self) -> None:
        """Legacy method for backward compatibility."""
        # Pydantic handles validation automatically

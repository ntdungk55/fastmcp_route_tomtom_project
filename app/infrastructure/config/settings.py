
import os
from dataclasses import dataclass

@dataclass(frozen=True)
class Settings:
    tomtom_base_url: str = os.getenv("TOMTOM_BASE_URL", "https://api.tomtom.com")
    tomtom_api_key: str = os.getenv("TOMTOM_API_KEY", "")
    http_timeout_sec: int = int(os.getenv("HTTP_TIMEOUT_SEC", "12"))

    def validate(self) -> None:
        if not self.tomtom_api_key:
            raise ValueError("TOMTOM_API_KEY is required")


from dataclasses import dataclass
from typing import Dict, Optional

from .http_method import HttpMethod


@dataclass(frozen=True)
class RequestEntity:
    method: HttpMethod
    url: str
    headers: dict[str, str]
    params: dict[str, str]
    json: dict | None
    timeout_sec: int

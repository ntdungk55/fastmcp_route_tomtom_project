
from dataclasses import dataclass
from typing import Optional, Dict
from .http_method import HttpMethod

@dataclass(frozen=True)
class RequestEntity:
    method: HttpMethod
    url: str
    headers: Dict[str, str]
    params: Dict[str, str]
    json: Optional[dict]
    timeout_sec: int

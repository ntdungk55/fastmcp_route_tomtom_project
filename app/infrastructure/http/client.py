
import aiohttp

from .http_method import HttpMethod
from .request_entity import RequestEntity


class AsyncApiClient:
    def __init__(self, default_headers: dict | None = None):
        self._default_headers = default_headers or {"Accept": "application/json"}

    async def send(self, req: RequestEntity) -> dict:
        headers = {**self._default_headers, **(req.headers or {})}
        timeout = aiohttp.ClientTimeout(total=req.timeout_sec)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            if req.method is HttpMethod.GET:
                async with session.get(req.url, headers=headers, params=req.params) as resp:
                    resp.raise_for_status()
                    return await resp.json()
            if req.method is HttpMethod.POST:
                async with session.post(req.url, headers=headers, params=req.params, json=req.json) as resp:
                    resp.raise_for_status()
                    return await resp.json()
            raise ValueError(f"Unsupported method: {req.method}")

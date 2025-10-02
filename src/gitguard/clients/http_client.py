from __future__ import annotations

import logging
import time
import requests

from dataclasses import dataclass
from typing import Any, Dict, Optional


try:
    import allure
    _HAS_ALLURE = True
except Exception:
    _HAS_ALLURE = False

logger = logging.getLogger("gitguard")


@dataclass
class HttpResult:
    """Result of an HTTP request."""
    status_code: int
    text: str
    json: Optional[Any]
    headers: Dict[str, Any]
    duration: float  # seconds

    def ok(self) -> bool:
        return 200 <= self.status_code < 300


class HttpClient:
    """
    Simple HTTP client wrapper with logging and optional Allure integration.
    """

    def __init__(self, base_url: str, timeout: int = 10, attach_to_allure: bool = True):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.attach_to_allure = attach_to_allure

    def _attach(self, name: str, content: str) -> None:
        if not (self.attach_to_allure and _HAS_ALLURE):
            return
        try:
            allure.attach(content, name=name, attachment_type=allure.attachment_type.TEXT)
        except Exception as e:
            logger.exception("Failed to attach HTTP log to Allure: %s", e)

    def _request(self, method: str, path: str, **kwargs) -> HttpResult:
        url = f"{self.base_url}/{path.lstrip('/')}"
        logger.debug("HTTP %s %s kwargs=%s", method.upper(), url, kwargs)

        start = time.perf_counter()
        resp = requests.request(method, url, timeout=self.timeout, **kwargs)
        duration = time.perf_counter() - start

        text = resp.text
        try:
            json_data = resp.json()
        except Exception:
            json_data = None

        result = HttpResult(
            status_code=resp.status_code,
            text=text,
            json=json_data,
            headers=dict(resp.headers),
            duration=duration,
        )

        logger.info("HTTP %s %s -> %s in %.3fs", method.upper(), url, resp.status_code, duration)

        # Attach to Allure
        if self.attach_to_allure:
            self._attach("http-request", f"{method.upper()} {url}\n\n{kwargs}")
            self._attach("http-response", f"Status: {resp.status_code}\n\n{text}")

        return result

    # Convenience wrappers
    def get(self, path: str, **kwargs) -> HttpResult:
        return self._request("get", path, **kwargs)

    def post(self, path: str, **kwargs) -> HttpResult:
        return self._request("post", path, **kwargs)

    def put(self, path: str, **kwargs) -> HttpResult:
        return self._request("put", path, **kwargs)

    def patch(self, path: str, **kwargs) -> HttpResult:
        return self._request("patch", path, **kwargs)

    def delete(self, path: str, **kwargs) -> HttpResult:
        return self._request("delete", path, **kwargs)

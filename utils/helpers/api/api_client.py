from __future__ import annotations

from typing import Any
from urllib.parse import urljoin

import requests


class ApiClient:
    def __init__(
        self,
        base_url: str,
        default_headers: dict[str, str] | None = None,
        timeout_seconds: float = 30,
    ) -> None:
        self.base_url = base_url.rstrip("/") + "/"
        self.timeout_seconds = timeout_seconds
        self.session = requests.Session()
        if default_headers:
            self.session.headers.update(default_headers)

    def request(self, method: str, path: str, **kwargs) -> requests.Response:
        kwargs.setdefault("timeout", self.timeout_seconds)
        return self.session.request(method, urljoin(self.base_url, path.lstrip("/")), **kwargs)

    def get(self, path: str, **kwargs) -> requests.Response:
        return self.request("GET", path, **kwargs)

    def post(self, path: str, json: dict[str, Any] | None = None, **kwargs) -> requests.Response:
        return self.request("POST", path, json=json, **kwargs)

    def delete(self, path: str, **kwargs) -> requests.Response:
        return self.request("DELETE", path, **kwargs)

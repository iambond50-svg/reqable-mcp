"""HTTP client for Reqable API."""

from __future__ import annotations

import json
from typing import Any

import httpx


class ReqableNotConnectedError(Exception):
    """Reqable is not running or cannot be reached."""

    def __init__(self, host: str, port: int) -> None:
        self.host = host
        self.port = port
        super().__init__(
            f"Reqable is not running or cannot be reached at {host}:{port}."
        )


class ReqableHttpError(Exception):
    """HTTP error from Reqable API."""

    def __init__(self, method: str, route: str, status_code: int, message: str) -> None:
        self.method = method
        self.route = route
        self.status_code = status_code
        self.message = message
        super().__init__(message)


class ReqableApiClient:
    """HTTP client for communicating with Reqable's local API."""

    def __init__(self, host: str, port: int) -> None:
        self.host = host
        self.port = port
        self._base_url = f"http://{host}:{port}"
        self._client = httpx.Client(
            timeout=httpx.Timeout(5.0),
            headers={"User-Agent": "reqable-mcp/2.0.0"},
        )

    def get(self, route: str) -> str:
        """Send a GET request to Reqable API and return the response body."""
        url = self._base_url + route
        try:
            response = self._client.get(url)
        except httpx.ConnectError as e:
            raise ReqableNotConnectedError(self.host, self.port) from e
        return self._handle_response("GET", route, response)

    def post(self, route: str, json_data: dict[str, Any] | None = None) -> str:
        """Send a POST request to Reqable API and return the response body."""
        url = self._base_url + route
        try:
            if json_data:
                response = self._client.post(url, json=json_data)
            else:
                response = self._client.post(url)
        except httpx.ConnectError as e:
            raise ReqableNotConnectedError(self.host, self.port) from e
        return self._handle_response("POST", route, response)

    @staticmethod
    def _handle_response(method: str, route: str, response: httpx.Response) -> str:
        body = response.text
        if response.status_code < 200 or response.status_code >= 300:
            try:
                msg = json.loads(body).get("message", body)
            except (json.JSONDecodeError, AttributeError):
                msg = body
            raise ReqableHttpError(method, route, response.status_code, msg)
        return body

    def close(self) -> None:
        self._client.close()

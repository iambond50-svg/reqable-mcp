"""Tools for managing Reqable REST WebSocket APIs."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from ..client import ReqableApiClient
from ..utils import (
    build_content_result,
    build_error_result,
    build_void_result,
    validate_string,
)


def register_rest_websocket_tools(mcp: FastMCP, client: ReqableApiClient) -> None:
    """Register all REST WebSocket API tools."""

    # --- create_from_url ---
    def create_from_url(name: str, url: str) -> str:
        err = validate_string({"name": name}, "name") or validate_string({"url": url}, "url")
        if err:
            return build_error_result(err).content[0].text
        return build_content_result(
            api_call=lambda: client.post("/rest/websocket/create/from-url", {"name": name, "url": url}),
            content_builder=lambda _: "Successfully created the WebSocket API from URL.",
        ).content[0].text

    create_from_url.__doc__ = "Create a new Reqable WebSocket API from a URL.\n\nArgs:\n    name: The WebSocket API name.\n    url: The URL to create the WebSocket API from."
    mcp.tool(name="rest_websocket_create_from_url", description="Create a new Reqable WebSocket API from a URL.")(create_from_url)

    # --- update ---
    def update(**kwargs) -> str:
        return build_void_result(
            api_call=lambda: client.post("/rest/websocket/update", kwargs),
            message="Successfully updated the WebSocket API.",
        ).content[0].text

    update.__doc__ = "Update an existing WebSocket API.\n\nArgs:\n    **kwargs: The full WebSocket API definition including id and all fields."
    mcp.tool(name="rest_websocket_update", description="Update an existing WebSocket API.")(update)

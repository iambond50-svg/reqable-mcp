"""Tools for managing Reqable REST HTTP APIs."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from ..client import ReqableApiClient
from ..utils import (
    build_content_result,
    build_error_result,
    build_void_result,
    validate_string,
)


def register_rest_http_tools(mcp: FastMCP, client: ReqableApiClient) -> None:
    """Register all REST HTTP API tools."""

    # --- create_from_url ---
    def create_from_url(name: str, url: str) -> str:
        err = validate_string({"name": name}, "name") or validate_string({"url": url}, "url")
        if err:
            return build_error_result(err).content[0].text
        return build_content_result(
            api_call=lambda: client.post("/rest/http/create/from-url", {"name": name, "url": url}),
            content_builder=lambda _: "Successfully created the HTTP API from URL.",
        ).content[0].text

    create_from_url.__doc__ = "Create a new Reqable HTTP API from a URL.\n\nArgs:\n    name: The HTTP API name.\n    url: The URL to create the HTTP API from."
    mcp.tool(name="rest_http_create_from_url", description="Create a new Reqable HTTP API from a URL.")(create_from_url)

    # --- create_from_curl ---
    def create_from_curl(name: str, curl: str) -> str:
        err = validate_string({"name": name}, "name") or validate_string({"curl": curl}, "curl")
        if err:
            return build_error_result(err).content[0].text
        return build_content_result(
            api_call=lambda: client.post("/rest/http/create/from-curl", {"name": name, "curl": curl}),
            content_builder=lambda _: "Successfully created the HTTP API from cURL.",
        ).content[0].text

    create_from_curl.__doc__ = "Create a new Reqable HTTP API from a cURL command.\n\nArgs:\n    name: The HTTP API name.\n    curl: The cURL command to create the HTTP API from."
    mcp.tool(name="rest_http_create_from_curl", description="Create a new Reqable HTTP API from a cURL command.")(create_from_curl)

    # --- update ---
    def update(**kwargs) -> str:
        return build_void_result(
            api_call=lambda: client.post("/rest/http/update", kwargs),
            message="Successfully updated the HTTP API.",
        ).content[0].text

    update.__doc__ = "Update an existing HTTP API.\n\nArgs:\n    **kwargs: The full HTTP API definition including id and all fields."
    mcp.tool(name="rest_http_update", description="Update an existing HTTP API.")(update)

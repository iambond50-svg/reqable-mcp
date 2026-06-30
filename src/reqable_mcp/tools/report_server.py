"""Report Server tools for the Reqable MCP server.

Registers 7 tools for managing the capture report server feature:
  get_config, set_enabled, lookup, set_item_enabled,
  create, delete, update
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from ..client import ReqableApiClient
from ..utils import (
    build_content_result,
    build_error_result,
    build_void_result,
    validate_bool,
    validate_string,
    validate_string_list,
)

_ROUTE_BASE = "/capture/report-server"
_ENCODING_ALLOWED = ["none", "gzip", "br", "zstd"]


def register_report_server_tools(mcp: FastMCP, client: ReqableApiClient) -> None:
    """Register all 7 report server tools."""

    # --- get_config ---
    def get_config() -> str:
        return build_content_result(
            api_call=lambda: client.get(_ROUTE_BASE),
            content_builder=lambda _: "Successfully retrieved report server configuration.",
        ).content[0].text

    get_config.__doc__ = "Get the current Reqable report server configuration for reporting matched traffic to external HTTP endpoints."
    mcp.tool(name="capture_report_server_get_config", description="Get the current Reqable report server configuration for reporting matched traffic to external HTTP endpoints.")(get_config)

    # --- set_enabled ---
    def set_enabled(enabled: bool) -> str:
        err = validate_bool({"enabled": enabled}, "enabled")
        if err:
            return build_error_result(err).content[0].text
        return build_void_result(
            api_call=lambda: client.post(f"{_ROUTE_BASE}/on" if enabled else f"{_ROUTE_BASE}/off"),
            message=f"Successfully {'enabled' if enabled else 'disabled'} the report server feature.",
        ).content[0].text

    set_enabled.__doc__ = "Enable or disable the Reqable report server feature globally without changing any existing report server definitions.\n\nArgs:\n    enabled: Whether to enable the report server feature."
    mcp.tool(name="capture_report_server_set_enabled", description="Enable or disable the Reqable report server feature globally without changing any existing report server definitions.")(set_enabled)

    # --- lookup ---
    def lookup(id: str) -> str:
        err = validate_string({"id": id}, "id")
        if err:
            return build_error_result(err).content[0].text
        return build_content_result(
            api_call=lambda: client.post(f"{_ROUTE_BASE}/lookup", {"id": id}),
            content_builder=lambda _: "Successfully retrieved the report server details.",
        ).content[0].text

    lookup.__doc__ = "Retrieve a report server by ID and return its full details.\n\nArgs:\n    id: The report server ID."
    mcp.tool(name="capture_report_server_lookup", description="Retrieve a report server by ID and return its full details.")(lookup)

    # --- set_item_enabled ---
    def set_item_enabled(ids: list[str], enabled: bool) -> str:
        err = validate_string_list({"ids": ids}, "ids") or validate_bool({"enabled": enabled}, "enabled")
        if err:
            return build_error_result(err).content[0].text
        return build_void_result(
            api_call=lambda: client.post(
                f"{_ROUTE_BASE}/enable" if enabled else f"{_ROUTE_BASE}/disable",
                {"ids": ids},
            ),
            message=f"Successfully {'enabled' if enabled else 'disabled'} the specified report servers.",
        ).content[0].text

    set_item_enabled.__doc__ = "Enable or disable one or more report servers by their IDs without changing their definitions.\n\nArgs:\n    ids: List of report server IDs.\n    enabled: Whether to enable the specified report servers."
    mcp.tool(name="capture_report_server_set_item_enabled", description="Enable or disable one or more report servers by their IDs without changing their definitions.")(set_item_enabled)

    # --- create ---
    def create(
        name: str,
        pattern: str,
        url: str,
        encoding: str,
        wildcard: bool | None = None,
        tag: str | None = None,
    ) -> str:
        err = validate_string({"name": name}, "name")
        if err:
            return build_error_result(err).content[0].text
        err = validate_string({"pattern": pattern}, "pattern")
        if err:
            return build_error_result(err).content[0].text
        err = validate_string({"url": url}, "url")
        if err:
            return build_error_result(err).content[0].text
        if not (url.startswith("http://") or url.startswith("https://")):
            return build_error_result("Invalid argument: url should be a valid http or https URL.").content[0].text
        err = validate_string({"encoding": encoding}, "encoding", allowed=_ENCODING_ALLOWED)
        if err:
            return build_error_result(err).content[0].text
        if wildcard is not None:
            err = validate_bool({"wildcard": wildcard}, "wildcard")
            if err:
                return build_error_result(err).content[0].text
        if tag is not None:
            err = validate_string({"tag": tag}, "tag", allow_empty=True)
            if err:
                return build_error_result(err).content[0].text
        kwargs: dict = {"name": name, "pattern": pattern, "url": url, "encoding": encoding}
        if wildcard is not None:
            kwargs["wildcard"] = wildcard
        if tag is not None:
            kwargs["tag"] = tag
        return build_content_result(
            api_call=lambda: client.post(f"{_ROUTE_BASE}/create", kwargs),
            content_builder=lambda _: "Successfully created the report server.",
        ).content[0].text

    create.__doc__ = "Create a new Reqable report server definition and return the created report server.\n\nArgs:\n    name: The human-readable name of the report server.\n    pattern: The URL or URL pattern, the matched traffic will be reported to the external endpoint.\n    url: The HTTP or HTTPS endpoint URL used to receive reported traffic.\n    encoding: The payload encoding used when sending traffic data (one of: none, gzip, br, zstd).\n    wildcard: Whether the traffic URL pattern is interpreted as a wildcard pattern.\n    tag: An optional tag value included in request header `x-reqable-reporter-tag`."
    mcp.tool(name="capture_report_server_create", description="Create a new Reqable report server definition and return the created report server.")(create)

    # --- delete ---
    def delete(ids: list[str]) -> str:
        err = validate_string_list({"ids": ids}, "ids")
        if err:
            return build_error_result(err).content[0].text
        return build_void_result(
            api_call=lambda: client.post(f"{_ROUTE_BASE}/delete", {"ids": ids}),
            message="Successfully deleted the specified report servers.",
        ).content[0].text

    delete.__doc__ = "Permanently delete one or more report servers by their IDs.\n\nArgs:\n    ids: List of report server IDs to delete."
    mcp.tool(name="capture_report_server_delete", description="Permanently delete one or more report servers by their IDs.")(delete)

    # --- update ---
    def update(**kwargs) -> str:
        return build_void_result(
            api_call=lambda: client.post(f"{_ROUTE_BASE}/update", kwargs),
            message="Successfully updated the report server.",
        ).content[0].text

    update.__doc__ = "Update an existing report server by ID.\n\nArgs:\n    **kwargs: The full report server definition including id and all fields."
    mcp.tool(name="capture_report_server_update", description="Update an existing report server by ID.")(update)

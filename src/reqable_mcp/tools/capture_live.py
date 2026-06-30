"""Capture Live tools for the Reqable MCP server.

A Python port of the official Dart reqable-mcp-server's `capture/live.dart`.
Registers 8 tools for inspecting and controlling Reqable's live capture engine.
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from ..client import ReqableApiClient
from ..utils import (
    build_content_result,
    build_error_result,
    build_void_result,
    validate_bool,
    validate_int,
    validate_string,
)


# The allowed values for a live capture filter's "type" field.
_ALLOWED_FILTER_TYPES = [
    "keyword",
    "url",
    "host",
    "ip",
    "method",
    "code",
    "application",
]


def _validate_filters(filters) -> str | None:
    """Validate the `filters` argument for capture_live_filter.

    Returns an error message string if invalid, or None if valid.
    """
    if filters is None:
        return "Missing required argument: filters."
    if not isinstance(filters, list):
        return "Invalid argument type: filters should be a list of filter objects."
    if not filters:
        return "Invalid argument: filters list should not be empty."
    for filter_obj in filters:
        if not isinstance(filter_obj, dict):
            return "Invalid argument: filters should contain only filter objects."
        err = validate_string(filter_obj, "type", allowed=_ALLOWED_FILTER_TYPES)
        if err:
            return err
    return None


def register_capture_live_tools(mcp: FastMCP, client: ReqableApiClient) -> None:
    """Register all 8 capture live tools with the FastMCP server."""

    # --- capture_live_status ---
    def capture_live_status() -> str:
        return build_content_result(
            api_call=lambda: client.get("/capture/live/status"),
            content_builder=lambda r: f"Reqable live capture is currently {r['status']}.",
        ).content[0].text

    capture_live_status.__doc__ = "Get whether Reqable live capture is currently active or inactive."
    mcp.tool(
        name="capture_live_status",
        description="Get whether Reqable live capture is currently active or inactive.",
    )(capture_live_status)

    # --- capture_live_set_enabled ---
    def capture_live_set_enabled(enabled: bool) -> str:
        err = validate_bool({"enabled": enabled}, "enabled")
        if err:
            return build_error_result(err).content[0].text
        return build_void_result(
            api_call=lambda: client.post(
                "/capture/live/on" if enabled else "/capture/live/off"
            ),
            message=f"Successfully {'started' if enabled else 'stopped'} live capture.",
        ).content[0].text

    capture_live_set_enabled.__doc__ = (
        "Start or stop Reqable live capture.\n\n"
        "Args:\n    enabled: Whether to start live capture."
    )
    mcp.tool(
        name="capture_live_set_enabled",
        description="Start or stop Reqable live capture.",
    )(capture_live_set_enabled)

    # --- capture_live_filter ---
    def capture_live_filter(filters: list) -> str:
        err = _validate_filters(filters)
        if err:
            return build_error_result(err).content[0].text
        return build_content_result(
            api_call=lambda: client.post("/capture/live/filter", {"filters": filters}),
            content_builder=lambda r: (
                f"Matched {len(r)} live capture record"
                f"{'s' if len(r) != 1 else ''}."
            ),
        ).content[0].text

    capture_live_filter.__doc__ = (
        "Filter current Reqable live capture records and return only the matching record IDs. "
        "Use `capture_live_get_by_id` with an ID to fetch the full record details.\n\n"
        "Args:\n    filters: A non-empty list of live capture filter objects. Each filter must "
        "have a \"type\" field (one of keyword, url, host, ip, method, code, application). "
        "Multiple filters are combined with logical AND."
    )
    mcp.tool(
        name="capture_live_filter",
        description=(
            "Filter current Reqable live capture records and return only the matching record IDs. "
            "Use `capture_live_get_by_id` with an ID to fetch the full record details."
        ),
    )(capture_live_filter)

    # --- capture_live_get_by_id ---
    def capture_live_get_by_id(id: int) -> str:
        err = validate_int({"id": id}, "id", minimum=0)
        if err:
            return build_error_result(err).content[0].text
        return build_content_result(
            api_call=lambda: client.post("/capture/live/get", {"id": id}),
            content_builder=lambda _: "Successfully retrieved the live capture record details.",
        ).content[0].text

    capture_live_get_by_id.__doc__ = (
        "Get the full details of a live capture record by numeric record ID.\n\n"
        "Args:\n    id: The numeric live capture record ID (>= 0)."
    )
    mcp.tool(
        name="capture_live_get_by_id",
        description="Get the full details of a live capture record by numeric record ID.",
    )(capture_live_get_by_id)

    # --- capture_live_clear ---
    def capture_live_clear() -> str:
        return build_void_result(
            api_call=lambda: client.post("/capture/live/clear"),
            message="Successfully cleared all live capture records.",
        ).content[0].text

    capture_live_clear.__doc__ = "Clear all currently retained Reqable live capture records."
    mcp.tool(
        name="capture_live_clear",
        description="Clear all currently retained Reqable live capture records.",
    )(capture_live_clear)

    # --- capture_live_generate_curl ---
    def capture_live_generate_curl(id: int) -> str:
        err = validate_int({"id": id}, "id", minimum=0)
        if err:
            return build_error_result(err).content[0].text
        return build_content_result(
            api_call=lambda: client.post("/capture/live/generate/curl", {"id": id}),
            content_builder=lambda _: (
                "Successfully generated cURL command for the live capture record."
            ),
        ).content[0].text

    capture_live_generate_curl.__doc__ = (
        "Generate a cURL command for a live capture record by numeric record ID.\n\n"
        "Args:\n    id: The numeric live capture record ID (>= 0)."
    )
    mcp.tool(
        name="capture_live_generate_curl",
        description="Generate a cURL command for a live capture record by numeric record ID.",
    )(capture_live_generate_curl)

    # --- capture_live_compose ---
    def capture_live_compose(id: int) -> str:
        err = validate_int({"id": id}, "id", minimum=0)
        if err:
            return build_error_result(err).content[0].text
        return build_content_result(
            api_call=lambda: client.post("/capture/live/compose", {"id": id}),
            content_builder=lambda _: (
                "Successfully composed the live capture record into a new Reqable tab."
            ),
        ).content[0].text

    capture_live_compose.__doc__ = (
        "Compose a completed live capture record into a new HTTP or WebSocket tab in Reqable "
        "and return the created API ID.\n\n"
        "Args:\n    id: The numeric live capture record ID (>= 0)."
    )
    mcp.tool(
        name="capture_live_compose",
        description=(
            "Compose a completed live capture record into a new HTTP or WebSocket tab in Reqable "
            "and return the created API ID."
        ),
    )(capture_live_compose)

    # --- capture_live_collection_add ---
    def capture_live_collection_add(
        id: int,
        collectionId: str,
        parentId: str | None = None,
        name: str | None = None,
    ) -> str:
        err = validate_int({"id": id}, "id", minimum=0)
        if err:
            return build_error_result(err).content[0].text
        err = validate_string({"collectionId": collectionId}, "collectionId")
        if err:
            return build_error_result(err).content[0].text
        body: dict = {"id": id, "collectionId": collectionId}
        if parentId is not None:
            body["parentId"] = parentId
        if name is not None:
            body["name"] = name
        return build_content_result(
            api_call=lambda: client.post("/capture/live/collection/add", body),
            content_builder=lambda _: (
                "Successfully added the live capture record to the collection."
            ),
        ).content[0].text

    capture_live_collection_add.__doc__ = (
        "Add a completed live capture record to an existing collection in Reqable and return "
        "the created API.\n\n"
        "Args:\n    id: The numeric live capture record ID (>= 0).\n"
        "    collectionId: The Reqable unique collection identifier.\n"
        "    parentId: Optional parent folder ID.\n"
        "    name: Optional name for the created API."
    )
    mcp.tool(
        name="capture_live_collection_add",
        description=(
            "Add a completed live capture record to an existing collection in Reqable and return "
            "the created API."
        ),
    )(capture_live_collection_add)

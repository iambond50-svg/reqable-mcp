"""Environment tools for the Reqable MCP server.

A Python port of the official Dart reqable-mcp-server environment tools.
Registers 8 tools for managing Reqable environments and built-in variables.
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from ..client import ReqableApiClient
from ..utils import (
    build_content_result,
    build_error_result,
    build_void_result,
    validate_string,
)


def register_environment_tools(mcp: FastMCP, client: ReqableApiClient) -> None:
    """Register all 8 environment tools with the FastMCP server."""

    # --- environment_list ---
    def environment_list() -> str:
        return build_content_result(
            api_call=lambda: client.get("/environment"),
            content_builder=lambda _: "Successfully retrieved the environments.",
        ).content[0].text

    environment_list.__doc__ = (
        "List all Reqable environments, including the global environment and "
        "user-defined environments, and indicate which environment is currently active."
    )
    mcp.tool(
        name="environment_list",
        description=(
            "List all Reqable environments, including the global environment and "
            "user-defined environments, and indicate which environment is currently active."
        ),
    )(environment_list)

    # --- environment_get_by_id ---
    def environment_get_by_id(id: str) -> str:
        err = validate_string({"id": id}, "id")
        if err:
            return build_error_result(err).content[0].text
        return build_content_result(
            api_call=lambda: client.post("/environment/get", {"id": id}),
            content_builder=lambda _: "Successfully retrieved the environment.",
        ).content[0].text

    environment_get_by_id.__doc__ = (
        "Get a Reqable environment by environment ID.\n\n"
        "Args:\n    id: The environment ID."
    )
    mcp.tool(
        name="environment_get_by_id",
        description="Get a Reqable environment by environment ID.",
    )(environment_get_by_id)

    # --- environment_get_active ---
    def environment_get_active() -> str:
        def _builder(r):
            if isinstance(r, dict) and r.get("environment") is None:
                return "No active environment is currently selected."
            return "Successfully retrieved the active environment."
        return build_content_result(
            api_call=lambda: client.get("/environment/get-active"),
            content_builder=_builder,
        ).content[0].text

    environment_get_active.__doc__ = "Get the currently active Reqable environment, if any."
    mcp.tool(
        name="environment_get_active",
        description="Get the currently active Reqable environment.",
    )(environment_get_active)

    # --- environment_create ---
    def environment_create(name: str) -> str:
        err = validate_string({"name": name}, "name")
        if err:
            return build_error_result(err).content[0].text
        return build_content_result(
            api_call=lambda: client.post("/environment/create", {"name": name}),
            content_builder=lambda _: "Successfully created the environment.",
        ).content[0].text

    environment_create.__doc__ = (
        "Create a new Reqable environment.\n\n"
        "Args:\n    name: The new environment name."
    )
    mcp.tool(
        name="environment_create",
        description="Create a new Reqable environment.",
    )(environment_create)

    # --- environment_update ---
    def environment_update(**kwargs) -> str:
        return build_void_result(
            api_call=lambda: client.post("/environment/update", kwargs),
            message="Successfully updated the environment.",
        ).content[0].text

    environment_update.__doc__ = (
        "Update a Reqable environment payload.\n\n"
        "Args:\n    **kwargs: The full environment definition including id and all fields."
    )
    mcp.tool(
        name="environment_update",
        description="Update a Reqable environment payload.",
    )(environment_update)

    # --- environment_delete ---
    def environment_delete(id: str) -> str:
        err = validate_string({"id": id}, "id")
        if err:
            return build_error_result(err).content[0].text
        return build_void_result(
            api_call=lambda: client.post("/environment/delete", {"id": id}),
            message="Successfully deleted the environment.",
        ).content[0].text

    environment_delete.__doc__ = (
        "Delete a Reqable environment by environment ID.\n\n"
        "Args:\n    id: The environment ID."
    )
    mcp.tool(
        name="environment_delete",
        description="Delete a Reqable environment by environment ID.",
    )(environment_delete)

    # --- environment_select ---
    def environment_select(id: str) -> str:
        err = validate_string({"id": id}, "id")
        if err:
            return build_error_result(err).content[0].text
        return build_void_result(
            api_call=lambda: client.post("/environment/select", {"id": id}),
            message="Successfully selected the environment.",
        ).content[0].text

    environment_select.__doc__ = (
        "Select a Reqable environment by environment ID.\n\n"
        "Args:\n    id: The environment ID to activate."
    )
    mcp.tool(
        name="environment_select",
        description="Select a Reqable environment by environment ID.",
    )(environment_select)

    # --- environment_builtin_variables ---
    def environment_builtin_variables() -> str:
        def _builder(r):
            count = len(r) if isinstance(r, list) else 0
            return f"Found {count} built-in variables."
        return build_content_result(
            api_call=lambda: client.get("/environment/built-in-variables"),
            content_builder=_builder,
        ).content[0].text

    environment_builtin_variables.__doc__ = (
        "List built-in environment variables exposed by Reqable."
    )
    mcp.tool(
        name="environment_builtin_variables",
        description="List built-in environment variables exposed by Reqable.",
    )(environment_builtin_variables)

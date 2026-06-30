"""Tools for retrieving Reqable script resources."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from ..client import ReqableApiClient
from ..utils import build_content_result


def register_script_tools(mcp: FastMCP, client: ReqableApiClient) -> None:
    """Register all script resource tools."""

    # --- framework ---
    def framework() -> str:
        return build_content_result(
            api_call=lambda: client.get("/script/framework"),
            content_builder=lambda c: str(c),
        ).content[0].text

    framework.__doc__ = "Get the Reqable script framework reference content."
    mcp.tool(name="script_framework", description="Get the Reqable script framework reference content.")(framework)

    # --- template ---
    def template() -> str:
        return build_content_result(
            api_call=lambda: client.get("/script/template"),
            content_builder=lambda c: str(c),
        ).content[0].text

    template.__doc__ = "Get the Reqable script template content."
    mcp.tool(name="script_template", description="Get the Reqable script template content.")(template)

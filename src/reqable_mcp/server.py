"""Reqable MCP Server – Python port of the official reqable-mcp-server.

Communicates with a running Reqable application via its local HTTP API
to expose 100+ MCP tools for capture, configuration, environment, and
REST testing operations.
"""

from __future__ import annotations

import sys

from mcp.server.fastmcp import FastMCP

from .client import ReqableApiClient
from .config import ReqableMcpConfig

# Tool module imports
from .tools.capture_live import register_capture_live_tools
from .tools.collection import register_collection_tools
from .tools.environment import register_environment_tools
from .tools.folder_tools import register_folder_tools
from .tools.profile_tools import register_profile_tools
from .tools.report_server import register_report_server_tools
from .tools.rest_http import register_rest_http_tools
from .tools.rest_websocket import register_rest_websocket_tools
from .tools.script_resources import register_script_tools

# ------------------------------------------------------------------
# Folder-based feature configurations (6 groups x 11 tools = 66 tools)
# ------------------------------------------------------------------

_FOLDER_FEATURES = [
    {
        "feature": "breakpoint",
        "feature_label": "Breakpoint",
        "feature_label_plural": "Breakpoints",
        "config_key": "breakpoints",
        "create_required": ["name", "url"],
        "create_validators": {
            "name": {"type": "string"},
            "url": {"type": "string"},
            "method": {"type": "string"},
            "wildcard": {"type": "bool"},
            "isRequestEnabled": {"type": "bool"},
            "isResponseEnabled": {"type": "bool"},
            "folderId": {"type": "string"},
        },
    },
    {
        "feature": "gateway",
        "feature_label": "Gateway",
        "feature_label_plural": "Gateways",
        "config_key": "gateways",
        "create_required": ["name", "action"],
        "create_validators": {
            "name": {"type": "string"},
            "action": {"type": "object"},
            "folderId": {"type": "string"},
        },
    },
    {
        "feature": "mirror",
        "feature_label": "Mirror",
        "feature_label_plural": "Mirrors",
        "config_key": "mirrors",
        "create_required": ["name", "pattern", "replacement"],
        "create_validators": {
            "name": {"type": "string"},
            "pattern": {"type": "string"},
            "replacement": {"type": "string"},
            "headerStrategy": {"type": "int", "min": 0, "max": 2},
            "sniStrategy": {"type": "int", "min": 0, "max": 2},
            "certStrategy": {"type": "int", "min": 0, "max": 2},
            "folderId": {"type": "string"},
        },
    },
    {
        "feature": "rewrite",
        "feature_label": "Rewrite",
        "feature_label_plural": "Rewrites",
        "config_key": "rewrites",
        "create_required": ["name", "url", "action"],
        "create_validators": {
            "name": {"type": "string"},
            "url": {"type": "string"},
            "action": {"type": "object"},
            "method": {"type": "string"},
            "wildcard": {"type": "bool"},
            "folderId": {"type": "string"},
        },
    },
    {
        "feature": "script",
        "feature_label": "Script",
        "feature_label_plural": "Scripts",
        "config_key": "scripts",
        "create_required": ["name", "url", "code"],
        "create_validators": {
            "name": {"type": "string"},
            "url": {"type": "string"},
            "code": {"type": "string"},
            "method": {"type": "string"},
            "wildcard": {"type": "bool"},
            "folderId": {"type": "string"},
        },
    },
    {
        "feature": "reverse-proxy",
        "feature_label": "Reverse Proxy",
        "feature_label_plural": "Reverse Proxies",
        "config_key": "reverseProxies",
        "create_required": ["name", "host"],
        "create_validators": {
            "name": {"type": "string"},
            "host": {"type": "string"},
            "localPort": {"type": "int", "min": 1024, "max": 65535},
            "security": {"type": "bool"},
            "preserveHost": {"type": "bool"},
            "folderId": {"type": "string"},
        },
    },
]

# ------------------------------------------------------------------
# Profile-based feature configurations (4 groups x 8 tools = 32 tools)
# ------------------------------------------------------------------

_PROFILE_FEATURES = [
    {
        "feature": "ssl-proxying",
        "feature_label": "SSL Proxying",
        "feature_label_plural": "SSL Proxying Profiles",
        "create_required": ["name", "rules"],
        "create_validators": {
            "name": {"type": "string"},
            "rules": {"type": "string_list"},
            "mode": {"type": "string", "allowed": ["include", "exclude"]},
            "silent": {"type": "bool"},
        },
    },
    {
        "feature": "network-throttling",
        "feature_label": "Network Throttling",
        "feature_label_plural": "Network Throttling Profiles",
        "create_required": ["name", "host", "mode"],
        "create_validators": {
            "name": {"type": "string"},
            "host": {"type": "string"},
            "mode": {
                "type": "string",
                "allowed": ["offline", "bad", "slow", "fast", "m2G", "m3G", "m4G", "m5G", "wifi"],
            },
        },
    },
    {
        "feature": "secondary-proxy",
        "feature_label": "Secondary Proxy",
        "feature_label_plural": "Secondary Proxy Profiles",
        "create_required": ["name", "host", "port"],
        "create_validators": {
            "name": {"type": "string"},
            "host": {"type": "string"},
            "port": {"type": "int", "min": 1, "max": 65535},
            "username": {"type": "string"},
            "password": {"type": "string"},
            "rules": {"type": "string_list"},
            "mode": {"type": "string", "allowed": ["include", "exclude"]},
        },
    },
    {
        "feature": "access-control",
        "feature_label": "Access Control",
        "feature_label_plural": "Access Control Profiles",
        "create_required": ["name", "rules"],
        "create_validators": {
            "name": {"type": "string"},
            "rules": {"type": "string_list"},
            "mode": {"type": "string", "allowed": ["include", "exclude"]},
        },
    },
]


def _create_server(config: ReqableMcpConfig) -> FastMCP:
    """Create a FastMCP server with all tools registered."""
    mcp = FastMCP(
        "reqable-mcp",
        instructions="Reqable MCP server exposing operations over Reqable APIs.",
    )
    client = ReqableApiClient(host=config.host, port=config.port)

    # Folder-based tools (6 groups x 11 = 66 tools)
    for feat in _FOLDER_FEATURES:
        register_folder_tools(mcp, client, **feat)

    # Profile-based tools (4 groups x 8 = 32 tools)
    for feat in _PROFILE_FEATURES:
        register_profile_tools(mcp, client, **feat)

    # Individual tool modules
    register_capture_live_tools(mcp, client)    # 8 tools
    register_environment_tools(mcp, client)      # 8 tools
    register_collection_tools(mcp, client)       # 15 tools
    register_rest_http_tools(mcp, client)        # 3 tools
    register_rest_websocket_tools(mcp, client)   # 2 tools
    register_script_tools(mcp, client)           # 2 tools
    register_report_server_tools(mcp, client)    # 7 tools

    return mcp


def main() -> None:
    """Run the MCP server over stdio."""
    config = ReqableMcpConfig.from_args(sys.argv[1:])
    mcp = _create_server(config)
    mcp.run(transport="stdio")

"""Configuration for Reqable MCP Server."""

from __future__ import annotations

import json
import os
import platform
from typing import Optional

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 9000


def _get_reqable_root() -> Optional[str]:
    """Get Reqable data root directory based on platform."""
    system = platform.system()
    if system == "Windows":
        appdata = os.environ.get("APPDATA")
        if appdata:
            return os.path.join(appdata, "Reqable")
    elif system == "Darwin":
        home = os.environ.get("HOME")
        if home:
            return os.path.join(home, "Library", "Application Support", "Reqable")
    elif system == "Linux":
        home = os.environ.get("HOME")
        if home:
            return os.path.join(home, ".local", "share", "Reqable")
    return None


def _resolve_app_port() -> Optional[int]:
    """Try to read proxyPort from Reqable's local config."""
    root = _get_reqable_root()
    if root is None:
        return None
    config_file = os.path.join(root, "config", "capture_config")
    if not os.path.exists(config_file):
        return None
    try:
        with open(config_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("proxyPort")
    except (json.JSONDecodeError, OSError):
        return None


class ReqableMcpConfig:
    """Configuration for the Reqable MCP server."""

    def __init__(self, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> None:
        self.host = host
        self.port = port

    @classmethod
    def from_args(cls, args: list[str]) -> "ReqableMcpConfig":
        """Parse command-line arguments."""
        host = DEFAULT_HOST
        port: Optional[int] = None

        i = 0
        while i < len(args):
            arg = args[i]
            if arg in ("--host", "-h") and i + 1 < len(args):
                host = args[i + 1]
                i += 2
            elif arg.startswith("--host="):
                host = arg.split("=", 1)[1]
                i += 1
            elif arg in ("--port", "-p") and i + 1 < len(args):
                port = int(args[i + 1])
                i += 2
            elif arg.startswith("--port="):
                port = int(arg.split("=", 1)[1])
                i += 1
            else:
                i += 1

        if port is None:
            port = _resolve_app_port() or DEFAULT_PORT

        return cls(host=host, port=port)

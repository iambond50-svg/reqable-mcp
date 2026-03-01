"""Reqable Capture Reader – MCP Server."""

from __future__ import annotations

import json
import logging
from typing import Any

from mcp.server.fastmcp import FastMCP

from .db import ReqableDB
from .models import (
    api_test_detail,
    api_test_summary,
    capture_detail,
    capture_summary,
    find_body_files,
    read_body,
)

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------
# Globals
# ------------------------------------------------------------------

mcp = FastMCP(
    "Reqable Capture Reader",
    instructions="Read and query Reqable packet capture records from the local database.",
)

_db: ReqableDB | None = None


def _get_db() -> ReqableDB:
    global _db
    if _db is None:
        _db = ReqableDB()
        _db.open()
    return _db


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

_MAX_LIMIT = 100
_DEFAULT_LIMIT = 20
_MAX_BODY_SIZE = 65536
_DEFAULT_BODY_SIZE = 4096


def _clamp_limit(limit: int | None) -> int:
    if limit is None:
        return _DEFAULT_LIMIT
    return max(1, min(limit, _MAX_LIMIT))


def _clamp_offset(offset: int | None) -> int:
    return max(0, offset or 0)


# ------------------------------------------------------------------
# Tool 1: list_captures
# ------------------------------------------------------------------

@mcp.tool()
def list_captures(
    host_filter: str | None = None,
    method_filter: str | None = None,
    code_filter: int | None = None,
    app_filter: str | None = None,
    keyword: str | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> str:
    """List proxy capture records with optional filters and pagination.

    Returns a JSON object with ``total`` (matching count) and ``items``
    (list of summaries for the current page).  Each item contains:
    id, method, host, port, path, protocol, code, app, timestamp.

    Args:
        host_filter: Filter by origin host (substring match, case-insensitive).
        method_filter: Filter by HTTP method (exact, case-insensitive).
        code_filter: Filter by HTTP status code.
        app_filter: Filter by application name (substring match, case-insensitive).
        keyword: Search in the URL path (substring match, case-insensitive).
        limit: Max items per page (default 20, max 100).
        offset: Number of items to skip (default 0).
    """
    lim = _clamp_limit(limit)
    off = _clamp_offset(offset)
    db = _get_db()

    matched: list[dict[str, Any]] = []
    for _, record in db.iter_captures():
        summary = capture_summary(record)

        # Filters
        if host_filter and host_filter.lower() not in (summary["host"] or "").lower():
            continue
        if method_filter and (summary["method"] or "").upper() != method_filter.upper():
            continue
        if code_filter is not None and summary["code"] != code_filter:
            continue
        if app_filter and app_filter.lower() not in (summary["app"] or "").lower():
            continue
        if keyword and keyword.lower() not in (summary["path"] or "").lower():
            continue

        matched.append(summary)

    total = len(matched)
    page = matched[off : off + lim]
    return json.dumps({"total": total, "limit": lim, "offset": off, "items": page}, ensure_ascii=False)


# ------------------------------------------------------------------
# Tool 2: get_capture_detail
# ------------------------------------------------------------------

@mcp.tool()
def get_capture_detail(id: int) -> str:
    """Get full details of a single capture record (headers, TLS, timing, app info).

    Does NOT include request/response body content — use ``get_capture_body``
    for that.

    Args:
        id: The capture record ID (from ``list_captures``).
    """
    db = _get_db()
    record = db.get_capture(id)
    if record is None:
        return json.dumps({"error": f"Capture record {id} not found."})
    return json.dumps(capture_detail(record), ensure_ascii=False)


# ------------------------------------------------------------------
# Tool 3: get_capture_body
# ------------------------------------------------------------------

@mcp.tool()
def get_capture_body(
    id: int,
    type: str = "response",
    max_size: int | None = None,
    prefer_decoded: bool = True,
) -> str:
    """Get the request or response body of a capture record.

    Args:
        id: The capture record ID.
        type: ``"request"`` or ``"response"``.
        max_size: Max bytes to return (default 4096, max 65536).
        prefer_decoded: If true, prefer the decompressed body file when available.
    """
    if type not in ("request", "response"):
        return json.dumps({"error": "type must be 'request' or 'response'."})

    cap = max(1, min(max_size or _DEFAULT_BODY_SIZE, _MAX_BODY_SIZE))

    db = _get_db()
    record = db.get_capture(id)
    if record is None:
        return json.dumps({"error": f"Capture record {id} not found."})

    files = find_body_files(db.capture_dir, record)
    candidates = files.get(type, [])

    if not candidates:
        return json.dumps({"error": f"No {type} body file found for record {id}."})

    # For response: first file is extract (decoded) if available
    if type == "response" and not prefer_decoded and len(candidates) > 1:
        # Skip the extract file, use raw
        filepath = candidates[-1]
    else:
        filepath = candidates[0]

    result = read_body(filepath, max_size=cap)
    return json.dumps(result, ensure_ascii=False)


# ------------------------------------------------------------------
# Tool 4: get_capture_stats
# ------------------------------------------------------------------

@mcp.tool()
def get_capture_stats() -> str:
    """Get aggregate statistics of all capture records.

    Returns counts grouped by host, HTTP method, status code, and
    application name.
    """
    db = _get_db()

    total = 0
    hosts: dict[str, int] = {}
    methods: dict[str, int] = {}
    codes: dict[str | int, int] = {}
    apps: dict[str, int] = {}

    for _, record in db.iter_captures():
        total += 1
        s = capture_summary(record)
        host = s["host"] or "unknown"
        method = s["method"] or "unknown"
        code = s["code"] if s["code"] is not None else "N/A"
        app = s["app"] or "unknown"

        hosts[host] = hosts.get(host, 0) + 1
        methods[method] = methods.get(method, 0) + 1
        codes[code] = codes.get(code, 0) + 1
        apps[app] = apps.get(app, 0) + 1

    def _top(d: dict, n: int = 20) -> list:
        return [{"name": k, "count": v} for k, v in sorted(d.items(), key=lambda x: -x[1])[:n]]

    return json.dumps({
        "total": total,
        "by_host": _top(hosts),
        "by_method": _top(methods),
        "by_code": _top(codes),
        "by_app": _top(apps),
    }, ensure_ascii=False)


# ------------------------------------------------------------------
# Tool 5: list_api_tests
# ------------------------------------------------------------------

@mcp.tool()
def list_api_tests(
    keyword: str | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> str:
    """List API test records (from Reqable's REST client) with optional search.

    Args:
        keyword: Search in the request URL (substring, case-insensitive).
        limit: Max items per page (default 20, max 100).
        offset: Number of items to skip (default 0).
    """
    lim = _clamp_limit(limit)
    off = _clamp_offset(offset)
    db = _get_db()

    matched: list[dict[str, Any]] = []
    for eid, record in db.iter_api_tests():
        summary = api_test_summary(eid, record)
        if keyword and keyword.lower() not in (summary["url"] or "").lower():
            continue
        matched.append(summary)

    total = len(matched)
    page = matched[off : off + lim]
    return json.dumps({"total": total, "limit": lim, "offset": off, "items": page}, ensure_ascii=False)


# ------------------------------------------------------------------
# Tool 6: get_api_test_detail
# ------------------------------------------------------------------

@mcp.tool()
def get_api_test_detail(id: int) -> str:
    """Get full details of a single API test record.

    Args:
        id: The API test entity ID (from ``list_api_tests``).
    """
    db = _get_db()
    record = db.get_api_test(id)
    if record is None:
        return json.dumps({"error": f"API test record {id} not found."})
    return json.dumps(api_test_detail(id, record), ensure_ascii=False)


# ------------------------------------------------------------------
# Entry point
# ------------------------------------------------------------------

def main() -> None:
    """Run the MCP server over stdio."""
    mcp.run(transport="stdio")

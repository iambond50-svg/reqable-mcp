"""Data parsing helpers for Reqable capture records."""

from __future__ import annotations

import glob
import os
from datetime import datetime, timezone
from typing import Any


# ------------------------------------------------------------------
# Safe nested access
# ------------------------------------------------------------------

def _g(obj: Any, *keys: str, default: Any = None) -> Any:
    """Safely traverse nested dicts; returns *default* on any miss or None."""
    for k in keys:
        if not isinstance(obj, dict):
            return default
        obj = obj.get(k)
        if obj is None:
            return default
    return obj


def _ts_to_iso(us: int | None) -> str | None:
    """Convert microsecond timestamp to ISO-8601 string."""
    if not us:
        return None
    try:
        return datetime.fromtimestamp(us / 1_000_000, tz=timezone.utc).isoformat()
    except (OSError, ValueError, OverflowError):
        return None


# ------------------------------------------------------------------
# Capture record -> summary dict  (used in list_captures)
# ------------------------------------------------------------------

def capture_summary(record: dict[str, Any]) -> dict[str, Any]:
    """Return a lightweight summary of a capture record."""
    s = record.get("session") or {}
    conn = s.get("connection") or {}
    req = (s.get("request") or {}).get("requestLine") or {}
    resp_sl = _g(s, "response", "statusLine") or {}
    app = record.get("appInfo") or {}

    return {
        "id": record.get("id"),
        "method": req.get("method", ""),
        "host": conn.get("originHost", ""),
        "port": conn.get("originPort", ""),
        "path": req.get("path", ""),
        "protocol": req.get("protocol", ""),
        "code": resp_sl.get("code"),
        "app": app.get("name", ""),
        "timestamp": _ts_to_iso(_g(s, "timestamp")),
    }


# ------------------------------------------------------------------
# Capture record -> detail dict  (used in get_capture_detail)
# ------------------------------------------------------------------

def _format_headers(headers: Any) -> list[dict[str, str]]:
    """Normalize header list to [{name, value}]."""
    if not isinstance(headers, list):
        return []
    result: list[dict[str, str]] = []
    for h in headers:
        if isinstance(h, dict):
            result.append({
                "name": h.get("name", h.get("key", "")),
                "value": str(h.get("value", "")),
            })
        elif isinstance(h, str):
            # "Name: Value" format
            parts = h.split(":", 1)
            result.append({
                "name": parts[0].strip(),
                "value": parts[1].strip() if len(parts) > 1 else "",
            })
    return result


def capture_detail(record: dict[str, Any]) -> dict[str, Any]:
    """Return the full detail of a capture record (no body content)."""
    s = record.get("session") or {}
    conn = s.get("connection") or {}
    req = s.get("request") or {}
    resp = s.get("response") or {}
    req_line = req.get("requestLine") or {}
    resp_sl = resp.get("statusLine") or {}
    app = record.get("appInfo") or {}

    # TLS info (simplified)
    tls_front = _g(conn, "frontend", "tls") or {}
    tls_back = _g(conn, "backend", "tls") or {}

    detail: dict[str, Any] = {
        "id": record.get("id"),
        "uid": record.get("uid"),
        "origin": record.get("origin"),
        "ssl_enabled": record.get("sslEnabled"),
        "ssl_bypassed": record.get("sslBypassed"),
        "comment": record.get("comment") or None,
        # Connection
        "connection": {
            "host": conn.get("originHost", ""),
            "port": conn.get("originPort", ""),
            "secure": conn.get("security", False),
            "tls_version": tls_front.get("version"),
            "cipher": _g(tls_front, "cipher", "name"),
            "sni": tls_front.get("sni"),
            "alpn": tls_back.get("selectedAlpn"),
        },
        # Request
        "request": {
            "method": req_line.get("method"),
            "path": req_line.get("path"),
            "protocol": req_line.get("protocol"),
            "header_size": req.get("headerSize"),
            "body_size": req.get("bodySize"),
            "start_time": _ts_to_iso(req.get("startTimestamp")),
            "end_time": _ts_to_iso(req.get("endTimestamp")),
            "headers": _format_headers(req.get("headers")),
        },
        # Response
        "response": {
            "code": resp_sl.get("code"),
            "message": resp_sl.get("message"),
            "protocol": resp_sl.get("protocol"),
            "header_size": resp.get("headerSize"),
            "body_size": resp.get("bodySize"),
            "start_time": _ts_to_iso(resp.get("startTimestamp")),
            "end_time": _ts_to_iso(resp.get("endTimestamp")),
            "headers": _format_headers(resp.get("headers")),
        },
        # App
        "app": {
            "name": app.get("name"),
            "process": app.get("id"),
            "path": app.get("path"),
            "pid": app.get("pid"),
        },
        "timestamp": _ts_to_iso(_g(s, "timestamp")),
    }
    return detail


# ------------------------------------------------------------------
# Body file helpers
# ------------------------------------------------------------------

def find_body_files(
    capture_dir: str,
    record: dict[str, Any],
) -> dict[str, list[str]]:
    """Find body files for a capture record.

    Returns ``{"request": [paths...], "response": [paths...]}``.
    """
    s = record.get("session") or {}
    timestamp = s.get("timestamp")
    conn_id = _g(s, "connection", "id")
    if not timestamp or not conn_id:
        return {"request": [], "response": []}

    pattern = os.path.join(capture_dir, f"{timestamp}-{conn_id}-*")
    files = sorted(glob.glob(pattern))

    result: dict[str, list[str]] = {"request": [], "response": []}
    for f in files:
        name = os.path.basename(f)
        if "req_raw-body" in name or "req-raw-body" in name:
            result["request"].append(f)
        elif "res-extract-body" in name:
            # Prefer decoded version — insert at front
            result["response"].insert(0, f)
        elif "res-raw-body" in name:
            result["response"].append(f)
    return result


def read_body(
    filepath: str,
    max_size: int = 4096,
) -> dict[str, Any]:
    """Read a body file with size cap.

    Returns ``{size, truncated, content, is_binary}``.
    """
    try:
        file_size = os.path.getsize(filepath)
    except OSError:
        return {"size": 0, "truncated": False, "content": "", "is_binary": False}

    try:
        with open(filepath, "rb") as fh:
            raw = fh.read(max_size)
    except OSError:
        return {"size": file_size, "truncated": False, "content": "<read error>", "is_binary": False}

    truncated = file_size > max_size

    # Try UTF-8
    try:
        text = raw.decode("utf-8")
        return {
            "size": file_size,
            "truncated": truncated,
            "content": text,
            "is_binary": False,
        }
    except UnicodeDecodeError:
        # Return hex representation for binary
        return {
            "size": file_size,
            "truncated": truncated,
            "content": raw.hex(),
            "is_binary": True,
        }


# ------------------------------------------------------------------
# API test record helpers
# ------------------------------------------------------------------

def api_test_summary(entity_id: int, record: dict[str, Any]) -> dict[str, Any]:
    """Lightweight summary of an API test record."""
    req = record.get("request") or {}
    resp = record.get("response") or {}
    return {
        "id": entity_id,
        "method": req.get("method", ""),
        "url": (req.get("url") or "")[:200],
        "code": resp.get("code"),
        "protocol": resp.get("protocol"),
        "mime": resp.get("mime"),
    }


def api_test_detail(entity_id: int, record: dict[str, Any]) -> dict[str, Any]:
    """Full detail of an API test record (cap large fields)."""
    # Deep-copy to avoid mutating cached data, but cap response body path
    detail = {
        "id": entity_id,
        "uuid": record.get("id"),
    }

    api = record.get("api")
    if isinstance(api, dict):
        detail["api"] = {
            "name": api.get("name"),
            "method": api.get("method"),
            "url": api.get("url"),
            "headers": api.get("headers"),
        }

    req = record.get("request")
    if isinstance(req, dict):
        detail["request"] = {
            "method": req.get("method"),
            "url": req.get("url"),
            "protocol": req.get("protocol"),
            "headers": req.get("headers"),
            "mime": req.get("mime"),
        }

    resp = record.get("response")
    if isinstance(resp, dict):
        detail["response"] = {
            "code": resp.get("code"),
            "message": resp.get("message"),
            "protocol": resp.get("protocol"),
            "headers": resp.get("headers"),
            "mime": resp.get("mime"),
            "body_path": resp.get("body"),
            "metrics": resp.get("metrics"),
        }

    return detail

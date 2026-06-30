"""Validation and result helpers for MCP tools."""

from __future__ import annotations

import json
from typing import Any

from mcp.types import CallToolResult, TextContent

from .client import ReqableApiClient


# ------------------------------------------------------------------
# Result builders
# ------------------------------------------------------------------

def build_content_result(
    api_call: callable,
    content_builder: callable,
) -> CallToolResult:
    """Call the API and return a CallToolResult with structured content."""
    try:
        result = api_call()
        parsed = json.loads(result)
        if isinstance(parsed, dict):
            structured = parsed
        elif isinstance(parsed, list):
            structured = {"items": parsed}
        else:
            structured = {"result": parsed}
        text = content_builder(parsed)
        return CallToolResult(
            content=[TextContent(type="text", text=text)],
            structuredContent=structured,
        )
    except Exception as e:
        return build_error_result(str(e))


def build_void_result(
    api_call: callable,
    message: str,
) -> CallToolResult:
    """Call the API (no return value needed) and return a success CallToolResult."""
    try:
        api_call()
        return CallToolResult(
            content=[TextContent(type="text", text=message)],
            structuredContent={"success": True, "message": message},
        )
    except Exception as e:
        return build_error_result(str(e))


def build_error_result(message: str) -> CallToolResult:
    """Build an error CallToolResult."""
    return CallToolResult(
        content=[TextContent(type="text", text=message)],
        isError=True,
    )


# ------------------------------------------------------------------
# Validation helpers
# ------------------------------------------------------------------

def validate_string(args: dict, key: str, *, allowed: list[str] | None = None, allow_empty: bool = False) -> str | None:
    """Validate a required string argument. Returns error message or None."""
    value = args.get(key)
    if value is None:
        return f"Missing required argument: {key}."
    if not isinstance(value, str):
        return f"Invalid argument type: {key} should be a string."
    if not allow_empty and not value:
        return f"Invalid argument: {key} should not be empty."
    if allowed is not None and value not in allowed:
        return f"Invalid argument: {key} should be one of [{', '.join(allowed)}]."
    return None


def validate_string_list(args: dict, key: str) -> str | None:
    """Validate a required list-of-strings argument. Returns error message or None."""
    value = args.get(key)
    if value is None:
        return f"Missing required argument: {key}."
    if not isinstance(value, list):
        return f"Invalid argument type: {key} should be a list of strings."
    if not value:
        return f"Invalid argument: {key} list should not be empty."
    if any(not isinstance(item, str) or not item.strip() for item in value):
        return f"Invalid argument: {key} should contain only non-empty strings."
    return None


def validate_bool(args: dict, key: str) -> str | None:
    """Validate a required boolean argument. Returns error message or None."""
    value = args.get(key)
    if value is None:
        return f"Missing required argument: {key}."
    if not isinstance(value, bool):
        return f"Invalid argument type: {key} should be a boolean."
    return None


def validate_int(args: dict, key: str, *, minimum: int | None = None, maximum: int | None = None) -> str | None:
    """Validate a required integer argument. Returns error message or None."""
    value = args.get(key)
    if value is None:
        return f"Missing required argument: {key}."
    if not isinstance(value, int) or isinstance(value, bool):
        return f"Invalid argument type: {key} should be an integer."
    if minimum is not None and value < minimum:
        return f"Invalid argument: {key} should be greater than or equal to {minimum}."
    if maximum is not None and value > maximum:
        return f"Invalid argument: {key} should be less than or equal to {maximum}."
    return None


def validate_object(args: dict, key: str) -> str | None:
    """Validate a required object/dict argument. Returns error message or None."""
    value = args.get(key)
    if value is None:
        return f"Missing required argument: {key}."
    if not isinstance(value, dict):
        return f"Invalid argument type: {key} should be an object."
    return None


def check_and_error(args: dict, validations: list[tuple[str, str | None]]) -> CallToolResult | None:
    """Run multiple validations, return first error as CallToolResult or None."""
    for _label, error in validations:
        if error is not None:
            return build_error_result(error)
    return None

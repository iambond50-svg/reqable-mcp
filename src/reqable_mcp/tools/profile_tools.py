"""Generic factory for profile-based tool groups.

Generates 8 tools for each group following the pattern:
  get_config, set_enabled, get_active, lookup, select, create, delete, update

Used by: ssl_proxying, network_throttling, secondary_proxy, access_control
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
    validate_string_list,
)


def register_profile_tools(
    mcp: FastMCP,
    client: ReqableApiClient,
    *,
    feature: str,          # e.g. "ssl-proxying", "network-throttling"
    feature_label: str,    # e.g. "SSL Proxying", "Network Throttling"
    feature_label_plural: str,
    create_required: list[str],
    create_validators: dict,
) -> None:
    """Register all 8 profile-based tools for a feature."""

    prefix = f"capture_{feature.replace('-', '_')}"
    route_base = f"/capture/{feature}"
    label_lower = feature_label.lower()

    # --- get_config ---
    def get_config() -> str:
        return build_content_result(
            api_call=lambda: client.get(route_base),
            content_builder=lambda _: f"Successfully retrieved {label_lower} configuration.",
        ).content[0].text

    get_config.__doc__ = f"Get the current Reqable {label_lower} configuration."
    mcp.tool(name=f"{prefix}_get_config", description=f"Get the current Reqable {label_lower} configuration.")(get_config)

    # --- set_enabled ---
    def set_enabled(enabled: bool) -> str:
        err = validate_bool({"enabled": enabled}, "enabled")
        if err:
            return build_error_result(err).content[0].text
        def _call():
            client.post(f"{route_base}/on" if enabled else f"{route_base}/off")
        return build_void_result(
            api_call=_call,
            message=f"Successfully {'enabled' if enabled else 'disabled'} the {label_lower} feature.",
        ).content[0].text

    set_enabled.__doc__ = f"Enable or disable the Reqable {label_lower} feature globally.\n\nArgs:\n    enabled: Whether to enable the {label_lower} feature."
    mcp.tool(name=f"{prefix}_set_enabled", description=f"Enable or disable the Reqable {label_lower} feature globally.")(set_enabled)

    # --- get_active ---
    def get_active() -> str:
        def _builder(r):
            if isinstance(r, dict) and r.get("profile") is None:
                return f"There is currently no active {label_lower} profile."
            return f"Successfully retrieved the active {label_lower} profile."
        return build_content_result(
            api_call=lambda: client.get(f"{route_base}/get-active"),
            content_builder=_builder,
        ).content[0].text

    get_active.__doc__ = f"Get the currently active {label_lower} profile, if any."
    mcp.tool(name=f"{prefix}_get_active", description=f"Get the currently active {label_lower} profile, if any.")(get_active)

    # --- lookup ---
    def lookup(id: str) -> str:
        err = validate_string({"id": id}, "id")
        if err:
            return build_error_result(err).content[0].text
        return build_content_result(
            api_call=lambda: client.post(f"{route_base}/lookup", {"id": id}),
            content_builder=lambda _: f"Successfully retrieved the {label_lower} profile details.",
        ).content[0].text

    lookup.__doc__ = f"Retrieve a {label_lower} profile by ID and return its full details.\n\nArgs:\n    id: The {label_lower} profile ID."
    mcp.tool(name=f"{prefix}_lookup", description=f"Retrieve a {label_lower} profile by ID and return its full details.")(lookup)

    # --- select ---
    def select(id: str) -> str:
        err = validate_string({"id": id}, "id")
        if err:
            return build_error_result(err).content[0].text
        return build_void_result(
            api_call=lambda: client.post(f"{route_base}/select", {"id": id}),
            message=f"Successfully selected the {label_lower} profile.",
        ).content[0].text

    select.__doc__ = f"Select a {label_lower} profile by ID as the active configuration.\n\nArgs:\n    id: The {label_lower} profile ID to activate."
    mcp.tool(name=f"{prefix}_select", description=f"Select a {label_lower} profile by ID as the active configuration.")(select)

    # --- create ---
    def create(**kwargs) -> str:
        for field_name in create_required:
            if field_name not in kwargs:
                return build_error_result(f"Missing required argument: {field_name}.").content[0].text
            vconf = create_validators.get(field_name, {})
            if vconf.get("type") == "string":
                err = validate_string({field_name: kwargs[field_name]}, field_name, allowed=vconf.get("allowed"))
            elif vconf.get("type") == "string_list":
                err = validate_string_list({field_name: kwargs[field_name]}, field_name)
            elif vconf.get("type") == "int":
                err = validate_int({field_name: kwargs[field_name]}, field_name, minimum=vconf.get("min"), maximum=vconf.get("max"))
            else:
                err = None
            if err:
                return build_error_result(err).content[0].text
        return build_content_result(
            api_call=lambda: client.post(f"{route_base}/create", kwargs),
            content_builder=lambda _: f"Successfully created the {label_lower} profile.",
        ).content[0].text

    create.__doc__ = f"Create a new Reqable {label_lower} profile and return the created profile.\n\nArgs:\n    **kwargs: The {label_lower} profile definition fields."
    mcp.tool(name=f"{prefix}_create", description=f"Create a new Reqable {label_lower} profile and return the created profile.")(create)

    # --- delete ---
    def delete(ids: list[str]) -> str:
        err = validate_string_list({"ids": ids}, "ids")
        if err:
            return build_error_result(err).content[0].text
        return build_void_result(
            api_call=lambda: client.post(f"{route_base}/delete", {"ids": ids}),
            message=f"Successfully deleted the specified {label_lower} profiles.",
        ).content[0].text

    delete.__doc__ = f"Permanently delete one or more {label_lower} profiles by their IDs.\n\nArgs:\n    ids: List of {label_lower} profile IDs to delete."
    mcp.tool(name=f"{prefix}_delete", description=f"Permanently delete one or more {label_lower} profiles by their IDs.")(delete)

    # --- update ---
    def update(**kwargs) -> str:
        return build_void_result(
            api_call=lambda: client.post(f"{route_base}/update", kwargs),
            message=f"Successfully updated the {label_lower} profile.",
        ).content[0].text

    update.__doc__ = f"Update an existing {label_lower} profile by ID.\n\nArgs:\n    **kwargs: The full {label_lower} profile definition including id and all fields."
    mcp.tool(name=f"{prefix}_update", description=f"Update an existing {label_lower} profile by ID.")(update)

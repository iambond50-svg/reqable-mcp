"""Generic factory for folder-based CRUD tool groups.

Generates 11 tools for each group following the pattern:
  get_config, set_enabled, list, set_item_enabled, get_by_id,
  create, create_folder, delete, delete_folder, update, update_folder_name

Used by: breakpoint, gateway, mirror, rewrite, script, reverse_proxy
"""

from __future__ import annotations

import json
from typing import Any

from mcp.server.fastmcp import FastMCP

from ..client import ReqableApiClient
from ..utils import (
    build_content_result,
    build_error_result,
    build_void_result,
    validate_bool,
    validate_int,
    validate_object,
    validate_string,
    validate_string_list,
)


def register_folder_tools(
    mcp: FastMCP,
    client: ReqableApiClient,
    *,
    feature: str,          # e.g. "breakpoint", "gateway"
    feature_label: str,    # e.g. "Breakpoint", "Gateway"
    feature_label_plural: str,  # e.g. "Breakpoints", "Gateways"
    config_key: str,       # key in config response, e.g. "breakpoints", "gateways"
    create_required: list[str],  # required fields for create, e.g. ["name", "url"]
    create_validators: dict,  # field -> validator config
) -> None:
    """Register all 11 folder-based CRUD tools for a feature."""

    prefix = f"capture_{feature.replace('-', '_')}"
    route_base = f"/capture/{feature}"
    label_lower = feature_label.lower()

    # --- get_config ---
    def _get_config() -> str:
        return client.get(route_base)

    def get_config() -> str:
        return build_content_result(
            api_call=_get_config,
            content_builder=lambda _: f"Successfully retrieved {feature_label.lower()} configuration.",
        ).content[0].text

    get_config.__doc__ = f"Get the current Reqable {feature_label.lower()} configuration."
    mcp.tool(name=f"{prefix}_get_config", description=f"Get the current Reqable {feature_label.lower()} configuration.")(get_config)

    # --- set_enabled ---
    def _set_enabled(enabled: bool) -> str:
        client.post(f"{route_base}/on" if enabled else f"{route_base}/off")
        return ""

    def set_enabled(enabled: bool) -> str:
        err = validate_bool({"enabled": enabled}, "enabled")
        if err:
            return build_error_result(err).content[0].text
        return build_void_result(
            api_call=lambda: _set_enabled(enabled),
            message=f"Successfully {'enabled' if enabled else 'disabled'} the {feature_label.lower()} feature.",
        ).content[0].text

    set_enabled.__doc__ = f"Enable or disable the Reqable {feature_label.lower()} feature globally.\n\nArgs:\n    enabled: Whether to enable the {feature_label.lower()} feature."
    mcp.tool(name=f"{prefix}_set_enabled", description=f"Enable or disable the Reqable {feature_label.lower()} feature globally.")(set_enabled)

    # --- list ---
    def _list() -> str:
        return client.get(f"{route_base}/list")

    def list_items() -> str:
        return build_content_result(
            api_call=_list,
            content_builder=lambda r: f"There are currently {len(r) if isinstance(r, list) else 0} {feature_label_plural.lower()} defined.",
        ).content[0].text

    list_items.__doc__ = f"List all Reqable {feature_label_plural.lower()} as a flat list. Folders are not returned as items."
    mcp.tool(name=f"{prefix}_list", description=f"List all Reqable {feature_label_plural.lower()} as a flat list.")(list_items)

    # --- set_item_enabled ---
    def _set_item_enabled(ids: list[str], enabled: bool) -> str:
        client.post(f"{route_base}/{'enable' if enabled else 'disable'}", {"ids": ids})
        return ""

    def set_item_enabled(ids: list[str], enabled: bool) -> str:
        err = validate_string_list({"ids": ids}, "ids") or validate_bool({"enabled": enabled}, "enabled")
        if err:
            return build_error_result(err).content[0].text
        return build_void_result(
            api_call=lambda: _set_item_enabled(ids, enabled),
            message=f"Successfully {'enabled' if enabled else 'disabled'} the specified {feature_label_plural.lower()}.",
        ).content[0].text

    set_item_enabled.__doc__ = f"Enable or disable one or more {feature_label_plural.lower()} by their IDs.\n\nArgs:\n    ids: List of {feature_label.lower()} IDs.\n    enabled: Whether to enable the specified {feature_label_plural.lower()}."
    mcp.tool(name=f"{prefix}_set_item_enabled", description=f"Enable or disable one or more {feature_label_plural.lower()} by their IDs.")(set_item_enabled)

    # --- get_by_id ---
    def _get_by_id(id: str) -> str:
        return client.post(f"{route_base}/lookup", {"id": id})

    def get_by_id(id: str) -> str:
        err = validate_string({"id": id}, "id")
        if err:
            return build_error_result(err).content[0].text
        return build_content_result(
            api_call=lambda: _get_by_id(id),
            content_builder=lambda _: f"Successfully retrieved the {feature_label.lower()} details.",
        ).content[0].text

    get_by_id.__doc__ = f"Retrieve a {feature_label.lower()} by ID and return its full details.\n\nArgs:\n    id: The {feature_label.lower()} ID."
    mcp.tool(name=f"{prefix}_get_by_id", description=f"Retrieve a {feature_label.lower()} by ID and return its full details.")(get_by_id)

    # --- create ---
    def _create(**kwargs) -> str:
        return client.post(f"{route_base}/create", kwargs)

    def create(**kwargs) -> str:
        # Validate required fields
        for field_name in create_required:
            vconf = create_validators.get(field_name, {})
            if field_name in kwargs:
                if vconf.get("type") == "string":
                    err = validate_string({field_name: kwargs[field_name]}, field_name, allowed=vconf.get("allowed"))
                elif vconf.get("type") == "string_list":
                    err = validate_string_list({field_name: kwargs[field_name]}, field_name)
                elif vconf.get("type") == "object":
                    err = validate_object({field_name: kwargs[field_name]}, field_name)
                elif vconf.get("type") == "bool":
                    err = validate_bool({field_name: kwargs[field_name]}, field_name)
                elif vconf.get("type") == "int":
                    err = validate_int({field_name: kwargs[field_name]}, field_name, minimum=vconf.get("min"), maximum=vconf.get("max"))
                else:
                    err = None
                if err:
                    return build_error_result(err).content[0].text
            else:
                return build_error_result(f"Missing required argument: {field_name}.").content[0].text
        return build_content_result(
            api_call=lambda: _create(**kwargs),
            content_builder=lambda _: f"Successfully created the {feature_label.lower()}.",
        ).content[0].text

    create.__doc__ = f"Create a new Reqable {feature_label.lower()} and return the created {feature_label.lower()}.\n\nArgs:\n    **kwargs: The {feature_label.lower()} definition fields."
    mcp.tool(name=f"{prefix}_create", description=f"Create a new Reqable {feature_label.lower()} and return the created {feature_label.lower()}.")(create)

    # --- create_folder ---
    def _create_folder(name: str) -> str:
        return client.post(f"{route_base}/folder/create", {"name": name})

    def create_folder(name: str) -> str:
        err = validate_string({"name": name}, "name")
        if err:
            return build_error_result(err).content[0].text
        return build_content_result(
            api_call=lambda: _create_folder(name),
            content_builder=lambda _: f"Successfully created the {feature_label.lower()} folder.",
        ).content[0].text

    create_folder.__doc__ = f"Create a new {feature_label.lower()} folder for organizing related {feature_label_plural.lower()}.\n\nArgs:\n    name: The folder name."
    mcp.tool(name=f"{prefix}_create_folder", description=f"Create a new {feature_label.lower()} folder.")(create_folder)

    # --- delete ---
    def _delete(ids: list[str]) -> str:
        client.post(f"{route_base}/delete", {"ids": ids})
        return ""

    def delete(ids: list[str]) -> str:
        err = validate_string_list({"ids": ids}, "ids")
        if err:
            return build_error_result(err).content[0].text
        return build_void_result(
            api_call=lambda: _delete(ids),
            message=f"Successfully deleted the specified {feature_label_plural.lower()}.",
        ).content[0].text

    delete.__doc__ = f"Permanently delete one or more {feature_label_plural.lower()} by their IDs.\n\nArgs:\n    ids: List of {feature_label.lower()} IDs to delete."
    mcp.tool(name=f"{prefix}_delete", description=f"Permanently delete one or more {feature_label_plural.lower()} by their IDs.")(delete)

    # --- delete_folder ---
    def _delete_folder(ids: list[str]) -> str:
        client.post(f"{route_base}/folder/delete", {"ids": ids})
        return ""

    def delete_folder(ids: list[str]) -> str:
        err = validate_string_list({"ids": ids}, "ids")
        if err:
            return build_error_result(err).content[0].text
        return build_void_result(
            api_call=lambda: _delete_folder(ids),
            message=f"Successfully deleted the specified {feature_label.lower()} folders.",
        ).content[0].text

    delete_folder.__doc__ = f"Permanently delete one or more {feature_label.lower()} folders by their IDs.\n\nArgs:\n    ids: List of folder IDs to delete."
    mcp.tool(name=f"{prefix}_delete_folder", description=f"Permanently delete one or more {feature_label.lower()} folders by their IDs.")(delete_folder)

    # --- update ---
    def _update(**kwargs) -> str:
        client.post(f"{route_base}/update", kwargs)
        return ""

    def update(**kwargs) -> str:
        return build_void_result(
            api_call=lambda: _update(**kwargs),
            message=f"Successfully updated the {feature_label.lower()}.",
        ).content[0].text

    update.__doc__ = f"Update an existing {feature_label.lower()} by ID.\n\nArgs:\n    **kwargs: The full {feature_label.lower()} definition including id and all fields."
    mcp.tool(name=f"{prefix}_update", description=f"Update an existing {feature_label.lower()} by ID.")(update)

    # --- update_folder_name ---
    def _update_folder_name(id: str, name: str) -> str:
        client.post(f"{route_base}/folder/rename", {"id": id, "name": name})
        return ""

    def update_folder_name(id: str, name: str) -> str:
        err = validate_string({"id": id}, "id") or validate_string({"name": name}, "name")
        if err:
            return build_error_result(err).content[0].text
        return build_void_result(
            api_call=lambda: _update_folder_name(id, name),
            message=f"Successfully updated the {feature_label.lower()} folder name.",
        ).content[0].text

    update_folder_name.__doc__ = f"Rename an existing {feature_label.lower()} folder by ID.\n\nArgs:\n    id: The folder ID.\n    name: The new folder name."
    mcp.tool(name=f"{prefix}_update_folder_name", description=f"Rename an existing {feature_label.lower()} folder by ID.")(update_folder_name)

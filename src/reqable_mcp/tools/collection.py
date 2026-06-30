"""Collection tools for the Reqable MCP server.

A Python port of the official Dart reqable-mcp-server collection tools.
Registers 15 tools for managing Reqable collections, folders, and APIs.
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from ..client import ReqableApiClient
from ..utils import (
    build_content_result,
    build_error_result,
    build_void_result,
    validate_object,
    validate_string,
)


def register_collection_tools(mcp: FastMCP, client: ReqableApiClient) -> None:
    """Register all 15 Reqable collection tools with the FastMCP server."""

    # --- collection_list ---
    def collection_list() -> str:
        return build_content_result(
            api_call=lambda: client.get("/collection/list"),
            content_builder=lambda r: f"Found {len(r) if isinstance(r, list) else 0} collections.",
        ).content[0].text

    collection_list.__doc__ = "List all Reqable collection IDs."
    mcp.tool(name="collection_list", description="List all Reqable collection IDs.")(collection_list)

    # --- collection_structure ---
    def collection_structure() -> str:
        return build_content_result(
            api_call=lambda: client.get("/collection/structure"),
            content_builder=lambda r: f"Retrieved the structure for {len(r) if isinstance(r, list) else 0} collections.",
        ).content[0].text

    collection_structure.__doc__ = (
        "Get the collection tree structure for all Reqable collections. "
        "The structure doesn't include the detailed node data."
    )
    mcp.tool(
        name="collection_structure",
        description="Get the collection tree structure for all Reqable collections. The structure doesn't include the detailed node data.",
    )(collection_structure)

    # --- collection_get ---
    def collection_get(id: str) -> str:
        err = validate_string({"id": id}, "id")
        if err:
            return build_error_result(err).content[0].text
        return build_content_result(
            api_call=lambda: client.post("/collection/get", {"id": id}),
            content_builder=lambda _: "Successfully retrieved the collection properties.",
        ).content[0].text

    collection_get.__doc__ = (
        "Get the properties of a Reqable collection by collection ID.\n\n"
        "Args:\n    id: The Reqable unique collection identifier."
    )
    mcp.tool(name="collection_get", description="Get the properties of a Reqable collection by collection ID.")(collection_get)

    # --- collection_create ---
    def collection_create(name: str) -> str:
        err = validate_string({"name": name}, "name")
        if err:
            return build_error_result(err).content[0].text
        return build_content_result(
            api_call=lambda: client.post("/collection/create", {"name": name}),
            content_builder=lambda _: "Successfully created the collection.",
        ).content[0].text

    collection_create.__doc__ = (
        "Create a new Reqable collection by name.\n\n"
        "Args:\n    name: The new collection name."
    )
    mcp.tool(name="collection_create", description="Create a new Reqable collection by name.")(collection_create)

    # --- collection_update ---
    def collection_update(id: str, **kwargs) -> str:
        return build_void_result(
            api_call=lambda: client.post("/collection/update", {"id": id, **kwargs}),
            message="Successfully updated the collection properties.",
        ).content[0].text

    collection_update.__doc__ = (
        "Update a Reqable collection properties, including name, inherited query, "
        "inherited headers, inherited script, inherited authorization, and documentation.\n\n"
        "Args:\n    id: The collection ID.\n    **kwargs: The collection properties payload."
    )
    mcp.tool(
        name="collection_update",
        description="Update a Reqable collection properties, including name, inherited query, inherited headers, inherited script, inherited authorization, and documentation.",
    )(collection_update)

    # --- collection_delete ---
    def collection_delete(id: str) -> str:
        err = validate_string({"id": id}, "id")
        if err:
            return build_error_result(err).content[0].text
        return build_void_result(
            api_call=lambda: client.post("/collection/delete", {"id": id}),
            message="Successfully deleted the collection.",
        ).content[0].text

    collection_delete.__doc__ = (
        "Delete a Reqable collection by collection ID.\n\n"
        "Args:\n    id: The collection ID to delete."
    )
    mcp.tool(name="collection_delete", description="Delete a Reqable collection by collection ID.")(collection_delete)

    # --- collection_folder_get ---
    def collection_folder_get(collectionId: str, id: str) -> str:
        err = validate_string({"collectionId": collectionId}, "collectionId")
        if err:
            return build_error_result(err).content[0].text
        err = validate_string({"id": id}, "id")
        if err:
            return build_error_result(err).content[0].text
        return build_content_result(
            api_call=lambda: client.post("/collection/folder/get", {"collectionId": collectionId, "id": id}),
            content_builder=lambda _: "Successfully retrieved the folder properties.",
        ).content[0].text

    collection_folder_get.__doc__ = (
        "Get a Reqable collection folder properties object by collection ID and folder ID.\n\n"
        "Args:\n    collectionId: The containing collection ID.\n    id: The folder ID."
    )
    mcp.tool(
        name="collection_folder_get",
        description="Get a Reqable collection folder properties object by collection ID and folder ID.",
    )(collection_folder_get)

    # --- collection_folder_create ---
    def collection_folder_create(collectionId: str, name: str, parentId: str | None = None) -> str:
        err = validate_string({"collectionId": collectionId}, "collectionId")
        if err:
            return build_error_result(err).content[0].text
        err = validate_string({"name": name}, "name")
        if err:
            return build_error_result(err).content[0].text
        payload = {"collectionId": collectionId, "name": name}
        if parentId is not None:
            payload["parentId"] = parentId
        return build_content_result(
            api_call=lambda: client.post("/collection/folder/create", payload),
            content_builder=lambda _: "Successfully created the folder.",
        ).content[0].text

    collection_folder_create.__doc__ = (
        "Create a new folder in a Reqable collection, optionally under a parent folder.\n\n"
        "Args:\n    collectionId: The containing collection ID.\n"
        "    name: The new folder name.\n    parentId: Optional parent folder ID."
    )
    mcp.tool(
        name="collection_folder_create",
        description="Create a new folder in a Reqable collection, optionally under a parent folder.",
    )(collection_folder_create)

    # --- collection_folder_update ---
    def collection_folder_update(collectionId: str, id: str, **kwargs) -> str:
        err = validate_string({"collectionId": collectionId}, "collectionId")
        if err:
            return build_error_result(err).content[0].text
        err = validate_string({"id": id}, "id")
        if err:
            return build_error_result(err).content[0].text
        return build_void_result(
            api_call=lambda: client.post("/collection/folder/update", {"collectionId": collectionId, "id": id, **kwargs}),
            message="Successfully updated the folder properties.",
        ).content[0].text

    collection_folder_update.__doc__ = (
        "Update a Reqable collection folder properties object.\n\n"
        "Args:\n    collectionId: The containing collection ID.\n"
        "    id: The folder ID.\n    **kwargs: The folder properties payload."
    )
    mcp.tool(
        name="collection_folder_update",
        description="Update a Reqable collection folder properties object.",
    )(collection_folder_update)

    # --- collection_folder_delete ---
    def collection_folder_delete(collectionId: str, id: str) -> str:
        err = validate_string({"collectionId": collectionId}, "collectionId")
        if err:
            return build_error_result(err).content[0].text
        err = validate_string({"id": id}, "id")
        if err:
            return build_error_result(err).content[0].text
        return build_void_result(
            api_call=lambda: client.post("/collection/folder/delete", {"collectionId": collectionId, "id": id}),
            message="Successfully deleted the folder.",
        ).content[0].text

    collection_folder_delete.__doc__ = (
        "Delete a folder from a Reqable collection.\n\n"
        "Args:\n    collectionId: The containing collection ID.\n    id: The folder ID to delete."
    )
    mcp.tool(
        name="collection_folder_delete",
        description="Delete a folder from a Reqable collection.",
    )(collection_folder_delete)

    # --- collection_api_get ---
    def collection_api_get(collectionId: str, id: str) -> str:
        err = validate_string({"collectionId": collectionId}, "collectionId")
        if err:
            return build_error_result(err).content[0].text
        err = validate_string({"id": id}, "id")
        if err:
            return build_error_result(err).content[0].text
        return build_content_result(
            api_call=lambda: client.post("/collection/api/get", {"collectionId": collectionId, "id": id}),
            content_builder=lambda _: "Successfully retrieved the API details.",
        ).content[0].text

    collection_api_get.__doc__ = (
        "Get a Reqable HTTP or WebSocket API details in a collection by collection ID and API ID.\n\n"
        "Args:\n    collectionId: The containing collection ID.\n    id: The API ID."
    )
    mcp.tool(
        name="collection_api_get",
        description="Get a Reqable HTTP or WebSocket API details in a collection by collection ID and API ID.",
    )(collection_api_get)

    # --- collection_api_create ---
    def collection_api_create(collectionId: str, curl: str, parentId: str | None = None) -> str:
        err = validate_string({"collectionId": collectionId}, "collectionId")
        if err:
            return build_error_result(err).content[0].text
        err = validate_string({"curl": curl}, "curl")
        if err:
            return build_error_result(err).content[0].text
        payload = {"collectionId": collectionId, "curl": curl}
        if parentId is not None:
            payload["parentId"] = parentId
        return build_content_result(
            api_call=lambda: client.post("/collection/api/create", payload),
            content_builder=lambda _: "Successfully created the API in the collection from cURL.",
        ).content[0].text

    collection_api_create.__doc__ = (
        "Create a new API in a Reqable collection from a cURL command.\n\n"
        "Args:\n    collectionId: The containing collection ID.\n"
        "    curl: The cURL command used to create the HTTP API.\n"
        "    parentId: Optional parent folder ID."
    )
    mcp.tool(
        name="collection_api_create",
        description="Create a new API in a Reqable collection from a cURL command.",
    )(collection_api_create)

    # --- collection_api_add ---
    def collection_api_add(collectionId: str, api: dict, parentId: str | None = None) -> str:
        err = validate_string({"collectionId": collectionId}, "collectionId")
        if err:
            return build_error_result(err).content[0].text
        err = validate_object({"api": api}, "api")
        if err:
            return build_error_result(err).content[0].text
        payload = {"collectionId": collectionId, "api": api}
        if parentId is not None:
            payload["parentId"] = parentId
        return build_content_result(
            api_call=lambda: client.post("/collection/api/add", payload),
            content_builder=lambda _: "Successfully added the API to the collection.",
        ).content[0].text

    collection_api_add.__doc__ = (
        "Add a created HTTP or WebSocket API into a Reqable collection.\n\n"
        "Args:\n    collectionId: The containing collection ID.\n"
        "    api: The HTTP or WebSocket API payload.\n"
        "    parentId: Optional parent folder ID."
    )
    mcp.tool(
        name="collection_api_add",
        description="Add a created HTTP or WebSocket API into a Reqable collection.",
    )(collection_api_add)

    # --- collection_api_update ---
    def collection_api_update(collectionId: str, api: dict) -> str:
        err = validate_string({"collectionId": collectionId}, "collectionId")
        if err:
            return build_error_result(err).content[0].text
        err = validate_object({"api": api}, "api")
        if err:
            return build_error_result(err).content[0].text
        return build_void_result(
            api_call=lambda: client.post("/collection/api/update", {"collectionId": collectionId, "api": api}),
            message="Successfully updated the API.",
        ).content[0].text

    collection_api_update.__doc__ = (
        "Update an existing HTTP or WebSocket API in a Reqable collection.\n\n"
        "Args:\n    collectionId: The containing collection ID.\n    api: The HTTP or WebSocket API payload."
    )
    mcp.tool(
        name="collection_api_update",
        description="Update an existing HTTP or WebSocket API in a Reqable collection.",
    )(collection_api_update)

    # --- collection_api_delete ---
    def collection_api_delete(collectionId: str, id: str) -> str:
        err = validate_string({"collectionId": collectionId}, "collectionId")
        if err:
            return build_error_result(err).content[0].text
        err = validate_string({"id": id}, "id")
        if err:
            return build_error_result(err).content[0].text
        return build_void_result(
            api_call=lambda: client.post("/collection/api/delete", {"collectionId": collectionId, "id": id}),
            message="Successfully deleted the API from the collection.",
        ).content[0].text

    collection_api_delete.__doc__ = (
        "Delete a HTTP or WebSocket API from a Reqable collection by collection ID and API ID.\n\n"
        "Args:\n    collectionId: The containing collection ID.\n    id: The API ID to delete."
    )
    mcp.tool(
        name="collection_api_delete",
        description="Delete a HTTP or WebSocket API from a Reqable collection by collection ID and API ID.",
    )(collection_api_delete)

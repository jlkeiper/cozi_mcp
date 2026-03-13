#!/usr/bin/env python3
"""
Cozi MCP Server - Local / stdio version

Drop-in replacement for server.py that reads credentials from environment
variables instead of Smithery's session config system.

Usage:
  1. Copy .env.example to .env and fill in your Cozi credentials.
  2. Add this server to your MCP client (e.g. Claude Desktop) using:

     {
       "mcpServers": {
         "cozi": {
           "command": "uv",
           "args": ["run", "python", "-m", "cozi_mcp.server_local"],
           "env": {
             "COZI_USERNAME": "your-email@example.com",
             "COZI_PASSWORD": "your-password"
           }
         }
       }
     }

  Or set COZI_USERNAME / COZI_PASSWORD in your shell environment and run:

     uv run python -m cozi_mcp.server_local
"""

import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from mcp.server.fastmcp import FastMCP

# Import from py-cozi-client>=1.3.0
from cozi_client import (
    CoziClient,
    CoziList,
    CoziAppointment,
    ListType,
    ItemStatus,
    CoziException,
    AuthenticationError,
)

# Patch: Cozi API now requires an apikey query parameter on the login endpoint.
# Without it, Cloudflare returns 408 Request Timeout.
# See: https://github.com/Wetzel402/py-cozi/pull/3
import inspect
_auth_source = inspect.getsource(CoziClient.authenticate)
if "apikey" not in _auth_source:
    _orig_make_request = CoziClient._make_request

    async def _patched_make_request(self, method, endpoint, **kwargs):
        if "/auth/login" in endpoint and "apikey=" not in endpoint:
            endpoint = endpoint + ("&" if "?" in endpoint else "?") + "apikey=coziwc|v251_production"
        return await _orig_make_request(self, method, endpoint, **kwargs)

    CoziClient._make_request = _patched_make_request

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("cozi-mcp")

# ── Credentials come from environment variables ──────────────────────────────
COZI_USERNAME = os.environ.get("COZI_USERNAME", "")
COZI_PASSWORD = os.environ.get("COZI_PASSWORD", "")

# Global client instance (one auth session for the lifetime of the process)
cozi_client: Optional[CoziClient] = None


async def get_cozi_client() -> CoziClient:
    """Get or create the authenticated Cozi client instance."""
    global cozi_client

    if cozi_client is None:
        if not COZI_USERNAME or not COZI_PASSWORD:
            raise AuthenticationError(
                "COZI_USERNAME and COZI_PASSWORD environment variables must be set."
            )
        cozi_client = CoziClient(COZI_USERNAME, COZI_PASSWORD)
        await cozi_client.authenticate()

    return cozi_client


# ── MCP server ────────────────────────────────────────────────────────────────
mcp = FastMCP("cozi-mcp")


# ── Family management ─────────────────────────────────────────────────────────

@mcp.tool()
async def get_family_members() -> List[Dict[str, Any]]:
    """Get all family members in the Cozi account.

    Returns a list of family member objects. Use the 'id' field from each
    member when specifying attendees for appointments.
    """
    try:
        client = await get_cozi_client()
        members = await client.get_family_members()
        return [m.model_dump() for m in members]
    except CoziException as e:
        logger.error(f"Cozi API error in get_family_members: {e}")
        raise


# ── List management ───────────────────────────────────────────────────────────

@mcp.tool()
async def get_lists() -> List[Dict[str, Any]]:
    """Get all lists (shopping and todo lists)."""
    try:
        client = await get_cozi_client()
        lists = await client.get_lists()
        return [lst.model_dump() for lst in lists]
    except CoziException as e:
        logger.error(f"Cozi API error in get_lists: {e}")
        raise


@mcp.tool()
async def get_lists_by_type(list_type: str) -> List[Dict[str, Any]]:
    """Get lists filtered by type.

    Args:
        list_type: 'shopping' or 'todo'
    """
    try:
        enum = ListType.SHOPPING if list_type.lower() == "shopping" else ListType.TODO
        client = await get_cozi_client()
        lists = await client.get_lists_by_type(enum)
        return [lst.model_dump() for lst in lists]
    except CoziException as e:
        logger.error(f"Cozi API error in get_lists_by_type: {e}")
        raise


@mcp.tool()
async def create_list(name: str, list_type: str) -> Dict[str, Any]:
    """Create a new list.

    Args:
        name: Name of the new list
        list_type: 'shopping' or 'todo'
    """
    try:
        enum = ListType.SHOPPING if list_type.lower() == "shopping" else ListType.TODO
        client = await get_cozi_client()
        new_list = await client.create_list(name, enum)
        return new_list.model_dump()
    except CoziException as e:
        logger.error(f"Cozi API error in create_list: {e}")
        raise


@mcp.tool()
async def delete_list(list_id: str) -> bool:
    """Delete an existing list.

    Args:
        list_id: ID of the list to delete
    """
    try:
        client = await get_cozi_client()
        return await client.delete_list(list_id)
    except CoziException as e:
        logger.error(f"Cozi API error in delete_list: {e}")
        raise


@mcp.tool()
async def update_list(list_obj: Dict[str, Any]) -> Dict[str, Any]:
    """Update an existing list (e.g. reorder items).

    Args:
        list_obj: List object dictionary to update
    """
    try:
        cozi_list = CoziList(**list_obj)
        client = await get_cozi_client()
        updated = await client.update_list(cozi_list)
        return updated.model_dump()
    except CoziException as e:
        logger.error(f"Cozi API error in update_list: {e}")
        raise


# ── Item management ───────────────────────────────────────────────────────────

@mcp.tool()
async def add_item(list_id: str, item_text: str) -> Dict[str, Any]:
    """Add an item to a list.

    Args:
        list_id: ID of the target list
        item_text: Text content of the new item
    """
    try:
        client = await get_cozi_client()
        updated = await client.add_item(list_id, item_text)
        return updated.model_dump()
    except CoziException as e:
        logger.error(f"Cozi API error in add_item: {e}")
        raise


@mcp.tool()
async def update_item_text(list_id: str, item_id: str, new_text: str) -> Dict[str, Any]:
    """Update the text of an existing list item.

    Args:
        list_id: ID of the list containing the item
        item_id: ID of the item to update
        new_text: New text for the item
    """
    try:
        client = await get_cozi_client()
        updated = await client.update_item_text(list_id, item_id, new_text)
        return updated.model_dump()
    except CoziException as e:
        logger.error(f"Cozi API error in update_item_text: {e}")
        raise


@mcp.tool()
async def mark_item(list_id: str, item_id: str, completed: bool) -> Dict[str, Any]:
    """Mark an item as complete or incomplete.

    Args:
        list_id: ID of the list containing the item
        item_id: ID of the item
        completed: True to mark complete, False to mark incomplete
    """
    try:
        status = ItemStatus.COMPLETE if completed else ItemStatus.INCOMPLETE
        client = await get_cozi_client()
        updated = await client.mark_item(list_id, item_id, status)
        return updated.model_dump()
    except CoziException as e:
        logger.error(f"Cozi API error in mark_item: {e}")
        raise


@mcp.tool()
async def remove_items(list_id: str, item_ids: List[str]) -> bool:
    """Remove one or more items from a list.

    Args:
        list_id: ID of the list
        item_ids: List of item IDs to remove
    """
    try:
        client = await get_cozi_client()
        return await client.remove_items(list_id, item_ids)
    except CoziException as e:
        logger.error(f"Cozi API error in remove_items: {e}")
        raise


# ── Calendar management ───────────────────────────────────────────────────────

@mcp.tool()
async def get_calendar(year: int, month: int) -> List[Dict[str, Any]]:
    """Get calendar appointments for a specific month.

    Args:
        year: e.g. 2025
        month: 1–12
    """
    try:
        client = await get_cozi_client()
        appointments = await client.get_calendar(year, month)
        return [a.model_dump() for a in appointments]
    except CoziException as e:
        logger.error(f"Cozi API error in get_calendar: {e}")
        raise


@mcp.tool()
async def create_appointment(
    subject: str,
    start_date: str,
    end_date: str,
    attendees: List[str] = None,
    all_day: bool = False,
    notes: str = "",
) -> Dict[str, Any]:
    """Create a new calendar appointment.

    Call get_family_members() first to obtain the correct attendee IDs.

    Args:
        subject: Appointment title
        start_date: ISO 8601 datetime string (e.g. "2025-06-01T10:00:00")
        end_date: ISO 8601 datetime string
        attendees: List of family-member IDs (optional)
        all_day: True for an all-day event
        notes: Extra notes
    """
    try:
        start_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
        end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))

        data: Dict[str, Any] = {
            "subject": subject,
            "start_day": start_dt.date(),
            "notes": notes,
            "attendees": attendees if attendees is not None else [],
        }
        if not all_day:
            data["start_time"] = start_dt.time()
            data["end_time"] = end_dt.time()

        appointment = CoziAppointment(**data)
        client = await get_cozi_client()
        created = await client.create_appointment(appointment)
        return created.model_dump()
    except CoziException as e:
        logger.error(f"Cozi API error in create_appointment: {e}")
        raise


@mcp.tool()
async def update_appointment(appointment_obj: Dict[str, Any]) -> Dict[str, Any]:
    """Update an existing calendar appointment.

    Retrieve the current appointment from get_calendar(), modify the fields
    you want to change, then pass the whole object here.

    Args:
        appointment_obj: Full appointment dictionary (from get_calendar or a prior call)
    """
    try:
        appointment = CoziAppointment(**appointment_obj)
        client = await get_cozi_client()
        updated = await client.update_appointment(appointment)
        return updated.model_dump()
    except CoziException as e:
        logger.error(f"Cozi API error in update_appointment: {e}")
        raise


@mcp.tool()
async def delete_appointment(appointment_id: str) -> bool:
    """Delete a calendar appointment.

    Args:
        appointment_id: ID of the appointment to delete
    """
    try:
        client = await get_cozi_client()
        return await client.delete_appointment(appointment_id)
    except CoziException as e:
        logger.error(f"Cozi API error in delete_appointment: {e}")
        raise


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    mcp.run()
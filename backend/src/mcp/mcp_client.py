"""
MCP client for WorkMate AI.

Connects to:
1. WorkMate local MCP server (stdio)
2. Google Workspace MCP server (stdio)

Google OAuth authorization and token refresh are handled separately.
"""

import sys

from langchain_mcp_adapters.client import MultiServerMCPClient

from backend.core.config import settings
from backend.core.logging import get_logger

logger = get_logger(__name__)


# ============================================================
# MCP CLIENT FACTORIES
# ============================================================

# Workmate MCP server
def create_workmate_mcp_client() -> MultiServerMCPClient:
    """Create a client for WorkMate's local stdio MCP server."""
    
    return MultiServerMCPClient(
        {
            "workmate": {
                "transport": "stdio",
                "command": sys.executable,
                "args": ["-m", "backend.src.mcp.workmate_mcp"],
            }
        }
    )


# Google workspace MCP server
def create_google_mcp_client():
    """Create a client for Google's hosted Gmail MCP server."""

    return MultiServerMCPClient(
        {
            "google_workspace": {
                "transport": "stdio",
                "command": sys.executable,
                "args": ["-m", "backend.src.mcp.google_mcp"],

            }
        }
    )


# ============================================================
# GOOGLE TOOLS
# ============================================================

_google_tools_cache: list | None = None

async def load_google_tools() -> list:
    """
    Load all tools exposed by the Google Workspace MCP server.

    The result is cached so Gmail and Calendar loaders do not
    start multiple MCP server processes.
    """
    global _google_tools_cache

    if _google_tools_cache is not None:
        return _google_tools_cache

    client = create_google_mcp_client()

    try:
        tools = await client.get_tools()

        _google_tools_cache = tools

        logger.info(
            "Loaded %d Google Workspace MCP tools: %s",
            len(tools),
            [tool.name for tool in tools],
        )

        return tools

    except Exception:
        logger.exception("Failed to load Google Workspace MCP tools")
        raise


# Gmail tools
async def load_gmail_tools() -> list:
    """Load Gmail tools exposed by the Google Workspace MCP server."""
    try:
        google_tools = await load_google_tools()

        gmail_tools = [
            tool for tool in google_tools
            if tool.name in {
                "search_emails",
                "read_email",
                "create_email_draft",
                "send_email",
            }
        ]

        logger.info(
            "Loaded %d Gmail MCP tools: %s",
            len(gmail_tools),
            [tool.name for tool in gmail_tools],
        )

        return gmail_tools

    except Exception:
        logger.exception("Failed to load Gmail MCP tools")
        raise


# Calendar Tools
async def load_calendar_tools() -> list:
    """Load Calendar tools exposed by the Google Workspace MCP server."""
    try:
        google_tools = await load_google_tools()

        calendar_tools = [
            tool for tool in google_tools
            if tool.name in {
                "list_calendar_events",
                "create_calendar_event",
            }
        ]

        logger.info(
            "Loaded %d Calendar MCP tools: %s",
            len(calendar_tools),
            [tool.name for tool in calendar_tools],
        )

        return calendar_tools

    except Exception:
        logger.exception("Failed to load Calendar MCP tools")
        raise


# ============================================================
# WORKMATE TOOLS
# ============================================================

async def load_workmate_tools() -> list:
    """Load tools exposed by WorkMate's local MCP server."""
    client = create_workmate_mcp_client()

    try:
        tools = await client.get_tools()

        logger.info(
            "Loaded %d WorkMate MCP tools: %s",
            len(tools),
            [tool.name for tool in tools],
        )

        return tools

    except Exception:
        logger.exception("Failed to load WorkMate MCP tools")
        raise



# ============================================================
# GROUPED TOOLS
# ============================================================
async def get_tools_by_server() -> dict[str, list]:
    """
    Load MCP tools and group them by server.

    Returns:
        {
            "workmate": [...],
            "gmail": [...],
            "google_calendar": [...],
        }
    """
    grouped: dict[str, list] = {
        "workmate": [],
        "gmail": [],
        "google_calendar": [],
    }

    grouped["workmate"] = await load_workmate_tools()
    grouped["gmail"] = await load_gmail_tools()
    grouped["google_calendar"] = await load_calendar_tools()

    return grouped
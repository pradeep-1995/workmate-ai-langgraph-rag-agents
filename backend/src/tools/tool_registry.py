"""
Central registry for WorkMate AI agent tools.

Groups discovered MCP tools by agent responsibility.
Authentication and authorization must be enforced separately.
"""

from backend.src.mcp.mcp_client import get_tools_by_server
from backend.core.logging import get_logger
logger = get_logger(__name__)


def index_tools(tools: list) -> dict:
    """Index tools by their actual MCP tool names."""
    logger.info(f"Indexing tools: {len(tools)}")
    return {tool.name: tool for tool in tools}


def require_tools(
    available_tools: dict,
    required_names: set[str],
    group_name: str,) -> list:

    """Return required tools or raise a descriptive error."""
    missing = required_names - available_tools.keys()

    if missing:
        raise ValueError(
            f"Missing {group_name} tools: {sorted(missing)}. "
            f"Available tools: {sorted(available_tools.keys())}"
        )

    return [
        available_tools[name]
        for name in sorted(required_names)
    ]



async def get_agent_tools() -> dict[str, list]:
    """Discover MCP tools and group them by agent responsibility."""

    logger.info("Discovering MCP tools for WorkMate AI agents...")
    
    tool_groups = await get_tools_by_server()

    workmate_tools = tool_groups["workmate"]
    gmail_tools = tool_groups["gmail"]
    calendar_tools = tool_groups["google_calendar"]

    workmate_by_name = index_tools(workmate_tools)
    gmail_by_name = index_tools(gmail_tools)
    calendar_by_name = index_tools(calendar_tools)


    # ----------------------------------------------------------
    # Task agent: manage individual saved tasks.
    # ----------------------------------------------------------
    task_tools = require_tools(
        workmate_by_name,
        {
            "create_task",
            "list_tasks",
            "update_task",
            "complete_task",
            "delete_task",
        },
        "Task",
    )

    # ----------------------------------------------------------
    # RAG agent: answer questions from the WorkMate knowledge base.
    # ----------------------------------------------------------
    rag_tools = require_tools(
        workmate_by_name,
        {
            "rag_tool",
        },
        "RAG",
    )

    # ----------------------------------------------------------
    # Planning agent: needs saved tasks plus calendar availability.
    # ----------------------------------------------------------
    planning_tools = [
        *require_tools(
            workmate_by_name,
            {
                "list_tasks",
            },
            "Planning",
        ),
        *require_tools(
            calendar_by_name,
            {
                "list_calendar_events",
                "create_calendar_event",
            },
            "Planning",
        ),
    ]

    # ----------------------------------------------------------
    # Communication agent: Gmail search, read, draft, and send.
    # ----------------------------------------------------------
    communication_tools = [
        *require_tools(
            gmail_by_name,
            {
                "search_emails",
                "read_email",
                "create_email_draft",
                "send_email",
            },
            "Communication",
        ),
        *require_tools(
            calendar_by_name,
            {
                "create_calendar_event",
                "list_calendar_events",
            },
            "Communication",
        ),
    ]


    logger.info(
        "Discovered tools - Task: %d, RAG: %d, Planning: %d, Communication: %d",
        len(task_tools),
        len(rag_tools),
        len(planning_tools),
        len(communication_tools)
    )
    return {
        "task": task_tools,
        "rag": rag_tools,
        "planning": planning_tools,
        "communication": communication_tools,
    }

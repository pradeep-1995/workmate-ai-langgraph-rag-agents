"""
WorkMate AI FastAPI application.

Initializes MCP tools, the LLM, and LangGraph once when the API starts.

Exposes chat and human-approval endpoints.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, Depends
from langgraph.types import Command
from langgraph.checkpoint.memory import MemorySaver

from backend.api.schemas import (
    ApprovalRequest,
    ChatRequest,
    ChatResponse,
)
from backend.src.assistant.llm import get_llm
from backend.src.graph.workflow import build_workmate_graph
from backend.src.tools.tool_registry import get_agent_tools


logger = logging.getLogger(__name__)


# --------------------------------------------------
# Authentication dependency
# --------------------------------------------------

async def get_current_user(request: Request) -> dict:
    """
    Get the authenticated user from authentication middleware.

    Your authentication middleware must populate request.state.user.
    Do not accept user identity from the request body.
    """

    user = getattr(request.state, "user", None)

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Authentication required.",
        )

    return user


# --------------------------------------------------
# Application lifespan
# --------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize WorkMate AI when the API starts."""

    logger.info("Starting WorkMate AI API...")

    try:
        agent_tools = await get_agent_tools()

        task_tools = agent_tools["task"]
        rag_tools = agent_tools["rag"]
        planning_tools = agent_tools["planning"]
        communication_tools = agent_tools["communication"]

        logger.info("MCP tools loaded:")

        for group_name, tools in agent_tools.items():
            logger.info(
                "%s: %s",
                group_name,
                [tool.name for tool in tools],
            )

        llm = get_llm()

        # Development checkpointer.
        # Replace with a persistent checkpointer for production.
        checkpointer = MemorySaver()

        app.state.workmate_graph = build_workmate_graph(
            llm=llm,
            task_tools=task_tools,
            rag_tools=rag_tools,
            planning_tools=planning_tools,
            communication_tools=communication_tools,
            checkpointer=checkpointer,
        )

        logger.info("WorkMate AI API is ready.")

        yield

    except Exception:
        logger.exception(
            "Failed to initialize WorkMate AI."
        )
        raise

    finally:
        logger.info("WorkMate AI API shutting down.")


app = FastAPI(
    title="WorkMate AI",
    description="Agentic AI productivity assistant API",
    version="1.0.0",
    lifespan=lifespan,
)


# --------------------------------------------------
# Helper functions
# --------------------------------------------------

def get_config(thread_id: str) -> dict:
    """Create LangGraph configuration for a conversation."""

    return {
        "configurable": {
            "thread_id": thread_id,
        }
    }


def get_latest_message(result: dict) -> str:
    """Extract the latest user-facing message."""

    messages = result.get("messages", [])

    if not messages:
        return ""

    content = getattr(messages[-1], "content", "")

    if isinstance(content, str):
        return content

    return str(content)


def get_pending_approval(result: dict) -> dict | None:
    """Extract approval details from graph interrupts."""

    interrupts = result.get("__interrupt__", [])

    if not interrupts:
        return None

    if len(interrupts) != 1:
        raise RuntimeError(
            "Multiple simultaneous approval interrupts "
            "are not supported by this API."
        )

    interrupt_data = getattr(
        interrupts[0],
        "value",
        {},
    )

    if isinstance(interrupt_data, dict):
        return interrupt_data

    return {
        "message": "An approval is required.",
        "actions": [],
    }


def build_response(result: dict) -> ChatResponse:
    """Convert LangGraph output into an API response."""

    approval = get_pending_approval(result)

    if approval is not None:
        return ChatResponse(
            status="approval_required",
            approval=approval,
        )

    return ChatResponse(
        status="completed",
        response=get_latest_message(result),
    )


async def has_pending_interrupt(
    graph,
    config: dict,
) -> bool:
    """Check whether a graph execution is waiting for approval."""

    snapshot = await graph.aget_state(config)

    for task in snapshot.tasks:
        if getattr(task, "interrupts", ()):
            return True

    return False


# --------------------------------------------------
# Health endpoint
# --------------------------------------------------

@app.get("/health")
async def health_check():
    """Check API availability."""

    return {
        "status": "healthy",
        "application": "WorkMate AI",
    }


# --------------------------------------------------
# Chat endpoint
# --------------------------------------------------

@app.post(
    "/chat",
    response_model=ChatResponse,
)
async def chat(
    request: ChatRequest,
    current_user: dict = Depends(get_current_user),
):
    """Send a user message to the WorkMate AI graph."""

    graph = app.state.workmate_graph

    config = get_config(request.thread_id)

    user_id = str(current_user["id"])

    # IMPORTANT:
    # Verify that this thread belongs to user_id using your
    # persistent conversation/thread ownership database.
    #
    # Do not rely on thread_id being secret or unguessable.

    initial_input = {
        "messages": [
            {
                "role": "user",
                "content": request.message,
            }
        ],
        "user_request": request.message,
        "user_context": {
            "user_id": user_id,
            "permissions": current_user.get(
                "permissions",
                [],
            ),
        },
    }

    try:
        result = await graph.ainvoke(
            initial_input,
            config=config,
        )

        return build_response(result)

    except HTTPException:
        raise

    except Exception:
        logger.exception(
            "WorkMate graph execution failed for user %s",
            user_id,
        )

        raise HTTPException(
            status_code=500,
            detail="WorkMate AI could not process your request.",
        )


# --------------------------------------------------
# Human approval endpoint
# --------------------------------------------------

@app.post(
    "/approval",
    response_model=ChatResponse,
)
async def submit_approval(
    request: ApprovalRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Resume a paused graph after validating the pending approval.

    The production implementation must also verify that the
    pending action belongs to this authenticated user.
    """

    graph = app.state.workmate_graph

    config = get_config(request.thread_id)

    user_id = str(current_user["id"])

    # IMPORTANT:
    # Verify thread ownership and pending-action ownership
    # against your database before resuming.

    try:
        pending = await has_pending_interrupt(
            graph,
            config,
        )

        if not pending:
            raise HTTPException(
                status_code=409,
                detail="No pending approval exists for this thread.",
            )

        result = await graph.ainvoke(
            Command(resume=request.decision),
            config=config,
        )

        return build_response(result)

    except HTTPException:
        raise

    except Exception:
        logger.exception(
            "Approval processing failed for user %s",
            user_id,
        )

        raise HTTPException(
            status_code=500,
            detail="Could not process the approval decision.",
        )
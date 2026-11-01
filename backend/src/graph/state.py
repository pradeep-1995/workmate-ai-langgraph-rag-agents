# src/graph/state.py

from typing import Annotated, Literal, NotRequired, TypedDict

from langgraph.graph import MessagesState
from langgraph.graph.message import add_messages


AgentName = Literal[
    "task",
    "rag",
    "planning",
    "communication",
]

ApprovalStatus = Literal[
    "pending",
    "approved",
    "rejected",
]


class UserContext(TypedDict):
    """
    Trusted identity context created by the application.

    Never populate this from untrusted LLM output.
    """
    user_id: str
    permissions: list[str]


class PendingAction(TypedDict):
    """Describes an operation requiring user approval."""
    action_id: str
    action_type: str
    description: str
    approval_status: ApprovalStatus


class WorkmateState(MessagesState):
    """
    Shared state for the WorkMate AI workflow.

    Stores conversation history, routing information,
    authenticated user context, and approval metadata.
    """

    # Original user request.
    user_request: NotRequired[str]

    # Agent selected by the router.
    selected_agent: NotRequired[AgentName | None]

    # Final user-facing response.
    result: NotRequired[str]

    # Trusted identity context from the application.
    # This is a reference to identity and permissions,
    # not a place to store credentials or OAuth tokens.
    user_context: NotRequired[UserContext]

    # Human-in-the-loop approval.
    approval_status: NotRequired[ApprovalStatus | None]
    pending_action: NotRequired[PendingAction | None]

    # Error information safe for application-level handling.
    error: NotRequired[str | None]
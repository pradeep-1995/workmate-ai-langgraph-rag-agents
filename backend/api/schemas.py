"""
Pydantic schemas for the WorkMate AI API.
"""

from typing import Literal

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Request body for sending a message to WorkMate AI."""

    message: str = Field(
        min_length=1,
        max_length=10000,
        description="User message sent to the WorkMate AI assistant.",
    )

    thread_id: str = Field(
        min_length=1,
        max_length=128,
        description="Persistent LangGraph conversation thread ID.",
    )


class ApprovalRequest(BaseModel):
    """Request body for approving or rejecting a pending action."""

    thread_id: str = Field(
        min_length=1,
        max_length=128,
        description="LangGraph conversation thread ID awaiting approval.",
    )

    decision: Literal["approved", "rejected"] = Field(
        description="Human decision for the pending action.",
    )


class ErrorResponse(BaseModel):
    """Standard error response."""

    detail: str = Field(
        description="Human-readable error message.",
    )


class ApprovalDetails(BaseModel):
    """Details of an action waiting for human approval."""

    message: str = Field(
        default="Approval is required.",
        description="Explanation shown to the user.",
    )

    actions: list[dict] = Field(
        default_factory=list,
        description="Tool calls that require approval.",
    )


class ChatResponse(BaseModel):
    """Response returned after a chat request."""

    status: Literal[
        "completed",
        "approval_required",
    ]

    response: str | None = Field(
        default=None,
        description="Assistant response when the workflow completes.",
    )

    approval: ApprovalDetails | None = Field(
        default=None,
        description="Pending approval details, if applicable.",
    )
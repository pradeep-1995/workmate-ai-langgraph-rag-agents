# src/graph/router.py

from typing import Literal

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from backend.src.graph.state import WorkmateState

from backend.core.logging import get_logger
logger = get_logger(__name__)

AgentName = Literal[
    "task",
    "rag",
    "planning",
    "communication",
]


class RouterDecision(BaseModel):
    """Structured routing decision."""

    agent: AgentName = Field(
        description="The agent that should handle the user's request."
    )


ROUTER_PROMPT = """
You are the supervisor router for WorkMate AI.

Select exactly one agent based on the user's current request.

Available agents:

1. task
   Use for creating, updating, deleting, completing, or listing tasks.

2. rag
   Use for questions about knowledge-base documents, uploaded files,
   retrieved information, or productivity concepts.

3. planning
   Use for planning schedules, checking calendar availability,
   creating calendar events, or organizing tasks into a schedule.

4. communication
   Use for searching emails, reading emails, drafting emails,
   and sending emails.

Routing rules:
- Select the agent whose responsibility best matches the request.
- Use the recent conversation context when the latest message depends
  on previous messages.
- For requests involving multiple operations, select the agent
  responsible for the first operation that should be performed.
- Do not execute tools or perform actions yourself.
- Do not make authorization decisions.
- Return only a valid structured routing decision.
"""


def _extract_message_content(message) -> str:
    """Extract readable text from a LangChain message."""

    content = getattr(message, "content", "")

    if isinstance(content, str):
        return content

    if isinstance(content, list):
        text_parts = []

        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                text_parts.append(block.get("text", ""))

        return "\n".join(text_parts)

    return ""


def _get_user_request(state: WorkmateState) -> str:
    """Get the current request, falling back to the latest human message."""

    user_request = state.get("user_request", "")

    if isinstance(user_request, str) and user_request.strip():
        return user_request.strip()

    messages = state.get("messages", [])

    for message in reversed(messages):
        if isinstance(message, HumanMessage):
            content = _extract_message_content(message)

            if content.strip():
                return content.strip()

    raise ValueError(
        "Cannot route the request: no user request or human message found."
    )


def _get_recent_messages(
        state: WorkmateState, 
        max_messages: int = 10,
        ) -> list:
    
    """Return the most recent conversation messages for routing context."""
    messages = state.get("messages", [])
    return messages[-max_messages:]


def build_router(llm):
    """
    Build the supervisor router.

    The router classifies a request and returns a state update.
    It does not execute tools or authorize operations.
    """
    router_llm = llm.with_structured_output(RouterDecision)

    async def router_node(state: WorkmateState) -> dict:
        user_request = _get_user_request(state)
        recent_messages = _get_recent_messages(state)

        decision = await router_llm.ainvoke(
            [
                SystemMessage(content=ROUTER_PROMPT),
                *recent_messages,
                HumanMessage(
                    content=(
                        f"Current user request:\n{user_request}\n\n"
                        "Return the correct agent."
                    )
                ),
            ]
        )

        if not isinstance(decision, RouterDecision):
            logger.error("Router returned an invalid decision: %r", decision)
            raise ValueError(
                "The router did not return a valid RouterDecision."
            )

        logger.info(
            "Router decision: user_request = %r, selected_agent = %s",
            user_request,
            decision.agent
        )

        return {
            "user_request": user_request,
            "selected_agent": decision.agent,
            "error": None,
        }

    return router_node


def route_to_agent(state: WorkmateState) -> AgentName:
    """Select the next graph node using the router's decision."""

    selected_agent = state.get("selected_agent")

    if selected_agent is None:
        raise ValueError(
            "No agent selected. Execute the router node before routing."
        )

    return selected_agent
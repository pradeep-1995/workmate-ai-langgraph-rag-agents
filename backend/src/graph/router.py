"""
Router node for WorkMate AI.

Classifies the user request and routes it to the correct agent.
"""

import json
import re

from backend.core.logging import get_logger

logger = get_logger(__name__)


VALID_AGENTS = {
    "task",
    "rag",
    "planning",
    "communication",
}


def build_router(llm):
    """
    Build the router node.

    Args:
        llm: Chat model.

    Returns:
        A router node function for LangGraph.
    """

    async def router_node(state: dict) -> dict:
        """
        Decide which specialist agent should handle the request.
        """

        messages = state.get("messages", [])

        if not messages:
            return {
                "router_decision": {
                    "agent": "rag",
                    "reason": "No user message was provided.",
                }
            }

        system_prompt = """
You are the router for WorkMate AI.

Choose exactly one agent to handle the user's request.

Return ONLY valid JSON in this exact format:

{
  "agent": "task",
  "reason": "short explanation"
}

Allowed values for agent:
- "task": create, update, complete, delete, or list tasks
- "rag": questions about documents, PDFs, product knowledge, workflows, policies, concepts, or factual information in the knowledge base
- "planning": plan work, check availability, schedule tasks, or combine tasks with calendar availability
- "communication": search/read/draft/send email, or create calendar events

If the request is ambiguous, choose the most likely agent.
Do not return markdown. Do not return explanations outside JSON.
"""

        try:
            response = await llm.ainvoke(
                [
                    {
                        "role": "system",
                        "content": system_prompt,
                    },
                    *messages,
                ]
            )

            raw_content = getattr(response, "content", "")

            decision = parse_router_response(raw_content)

        except Exception:
            logger.exception("Router LLM call failed")

            decision = {
                "agent": "rag",
                "reason": (
                    "Router failed, so the request was sent to the RAG agent."
                ),
            }

        logger.info(
            "Router decision: %s | %s",
            decision["agent"],
            decision["reason"],
        )

        return {
            "router_decision": decision,
        }

    return router_node


def parse_router_response(raw_content: str) -> dict:
    """
    Parse the router response safely.

    Always returns a valid routing decision.
    """

    fallback = {
        "agent": "rag",
        "reason": "Router response could not be parsed.",
    }

    if not raw_content:
        logger.warning("Router returned empty content.")
        return fallback

    content = raw_content.strip()

    # Remove Markdown code fences if the model adds them.
    content = re.sub(
        r"^```(?:json)?\s*|\s*```$",
        "",
        content,
        flags=re.IGNORECASE,
    ).strip()

    try:
        data = json.loads(content)

        agent = str(data.get("agent", "")).strip().lower()
        reason = str(data.get("reason", "")).strip()

        if agent in VALID_AGENTS:
            return {
                "agent": agent,
                "reason": reason or "No reason provided.",
            }

        logger.warning("Invalid router agent: %s", agent)

        return fallback

    except (json.JSONDecodeError, TypeError, AttributeError):
        logger.warning(
            "Router returned non-JSON content: %s",
            content[:300],
        )
        return fallback


def route_to_agent(state: dict) -> str:
    """
    Convert the router decision into the next LangGraph node.
    """

    decision = state.get("router_decision")

    if not decision:
        logger.warning("No router decision found. Using RAG fallback.")
        return "rag"

    agent = decision.get("agent")

    if agent not in VALID_AGENTS:
        logger.warning(
            "Invalid router decision: %s. Using RAG fallback.",
            agent,
        )
        return "rag"

    return agent
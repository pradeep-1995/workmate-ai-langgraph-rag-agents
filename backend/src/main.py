# backend/src/main.py

"""
WorkMate AI CLI application.

Initializes MCP tools, builds the LangGraph workflow,
and runs a terminal chat session with human approval.
"""

import asyncio

from langgraph.types import Command

from backend.src.assistant.llm import get_llm
from backend.src.graph.workflow import build_workmate_graph
from backend.src.tools.tool_registry import get_agent_tools

async def ask_user(prompt: str) -> str:
    """ Read terminal input without blocking the async event loop."""
    return await asyncio.to_thread(input, prompt)


async def show_approval_request(interrupt_data: dict) -> str:
    """ Display the requested action and collect a decision."""

    print("\n" + "=" * 60)
    print("ACTION REQUIRES YOUR APPROVAL")
    print("=" * 60)

    print(interrupt_data.get(
        "message",
        "Approval is required.",)
    )

    for action in interrupt_data.get("actions", []):
        print(f"\nTool: {action.get('tool')}")
        print("Arguments:")

        for key, value in action.get("arguments", {}).items():
            print(f"  {key}: {value}")

    print("\nReview the details carefully.")


    while True:
        choice = (
            await asyncio.to_thread(
                input,
                "Approve this action? (yes/no): ",
            )
        ).strip().lower()

        if choice in {"yes", "y"}:
            return "approved"

        if choice in {"no", "n"}:
            return "rejected"

        print("Please enter yes or no.")


async def run_until_complete(
    app,
    initial_input: dict,
    config: dict,
) -> dict:
    """
    Run the graph until completion or until all approvals are resolved.
    """

    result = await app.ainvoke(
        initial_input,
        config=config,
    )

    while result.get("__interrupt__"):
        interrupts = result["__interrupt__"]

        if len(interrupts) != 1:
            raise RuntimeError(
                "Expected exactly one pending approval interrupt."
            )

        interrupt_item = interrupts[0]
        interrupt_data = getattr(interrupt_item, "value", {})

        if not isinstance(interrupt_data, dict):
            raise RuntimeError(
                "Unexpected interrupt format. "
                "The workflow was not resumed."
            )

        resume_value = await show_approval_request(interrupt_data)

        result = await app.ainvoke(
            Command(resume=resume_value),
            config=config,
        )

    return result


def print_agent_response(result: dict) -> None:
    """Print the latest user-facing message from the graph."""

    messages = result.get("messages", [])

    if not messages:
        print("\nWorkMate AI: The workflow finished without a message.")
        return

    last_message = messages[-1]
    content = getattr(last_message, "content", "")

    if content:
        print(f"\nWorkMate AI: {content}")
    else:
        print(
            "\nWorkMate AI: The workflow completed "
            "without a text response."
        )


async def main() -> None:
    """Initialize MCP tools, build the graph, and start the CLI."""

    print("Starting WorkMate AI...")

    # --------------------------------------------------
    # 1. Load and validate MCP tools
    # --------------------------------------------------
    agent_tools = await get_agent_tools()

    task_tools = agent_tools["task"]
    rag_tools = agent_tools["rag"]
    planning_tools = agent_tools["planning"]
    communication_tools = agent_tools["communication"]

    print("\nConnected MCP tool groups:")

    print(
        f"- Task Agent: "
        f"{[tool.name for tool in task_tools]}"
    )

    print(
        f"- RAG Agent: "
        f"{[tool.name for tool in rag_tools]}"
    )

    print(
        f"- Planning Agent: "
        f"{[tool.name for tool in planning_tools]}"
    )

    print(
        f"- Communication Agent: "
        f"{[tool.name for tool in communication_tools]}"
    )

    # --------------------------------------------------
    # 2. Initialize the LLM
    # --------------------------------------------------
    llm = get_llm()

    # --------------------------------------------------
    # 3. Build the LangGraph workflow
    # --------------------------------------------------
    app = build_workmate_graph(
        llm=llm,
        task_tools=task_tools,
        rag_tools=rag_tools,
        planning_tools=planning_tools,
        communication_tools=communication_tools,
    )

    # Use a stable thread ID for this terminal session.
    config = {
        "configurable": {
            "thread_id": "workmate-terminal-session-1",
        }
    }

    print("\nWorkMate AI is ready.")
    print("Type 'exit' or 'quit' to stop.\n")

    # --------------------------------------------------
    # 4. Terminal chat loop
    # --------------------------------------------------
    while True:
        try:
            user_request = await ask_user("You: ")

        except (EOFError, KeyboardInterrupt):
            print("\nExiting WorkMate AI.")
            break

        user_request = user_request.strip()

        if user_request.lower() in {"exit", "quit"}:
            print("Goodbye!")
            break

        if not user_request:
            continue

        initial_input = {
            "messages": [
                {
                    "role": "user",
                    "content": user_request,
                }
            ],
            "user_request": user_request,
            "user_context": {
                "user_id": "local_user",
                "permissions": [
                    "tasks:read",
                    "tasks:write",
                    "knowledge:read",
                    "gmail:read",
                    "gmail:draft",
                    "gmail:send",
                    "calendar:read",
                    "calendar:write",
                ],
            },
        }

        try:
            result = await run_until_complete(
                app=app,
                initial_input=initial_input,
                config=config,
            )

            print_agent_response(result)

        except KeyboardInterrupt:
            print(
                "\nInterrupted. Check the saved graph state "
                "before retrying any pending operation."
            )

        except Exception as exc:
            print(
                f"\nAn error occurred: "
                f"{type(exc).__name__}: {exc}"
            )


if __name__ == "__main__":
    asyncio.run(main())
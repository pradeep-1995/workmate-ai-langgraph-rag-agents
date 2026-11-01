
import asyncio

from langchain_core.messages import HumanMessage
from langchain_core.tools import tool
from langgraph.graph import END, StateGraph
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command

from backend.src.graph.state import WorkmateState
from backend.src.agents.communication_agent import (
    build_communication_agent_nodes,
)


# Mock email tool. It does not send a real email.
@tool
def send_email(
    recipient: str,
    subject: str,
    body: str,
) -> str:
    """Send an email to the specified recipient."""
    return (
        f"Mock email sent successfully to {recipient}. "
        f"Subject: {subject}"
    )


def route_after_approval(state: WorkmateState):
    if state.get("approval_status") == "approved":
        return "tools"

    return "reject"


async def main():
    # Replace with your actual LLM initialization import.
    from backend.src.assistant.llm import get_llm
    llm = get_llm()


    communication_tools = [send_email]

    (
        communication_agent_node,
        approval_node,
        reject_tool_calls_node,
        communication_tools_node,
    ) = build_communication_agent_nodes(
        llm=llm,
        communication_tools=communication_tools,
    )

    # Build a small test graph.
    builder = StateGraph(WorkmateState)

    builder.add_node("communication_agent", communication_agent_node)
    builder.add_node("approval", approval_node)
    builder.add_node("reject", reject_tool_calls_node)
    builder.add_node("tools", communication_tools_node)

    builder.set_entry_point("communication_agent")

    builder.add_edge("communication_agent", "approval")

    builder.add_conditional_edges(
        "approval",
        route_after_approval,
        {
            "tools": "tools",
            "reject": "reject",
        },
    )

    builder.add_edge("tools", END)
    builder.add_edge("reject", END)

    # interrupt() requires a checkpointer.
    checkpointer = MemorySaver()

    graph = builder.compile(checkpointer=checkpointer)

    # Unique thread ID for this test run.
    config = {
        "configurable": {
            "thread_id": "communication-agent-test"
        }
    }

    initial_state = {
        "messages": [
            HumanMessage(
                content=(
                    "Send an email to test@example.com. "
                    "Subject: WorkMate AI Test. "
                    "Body: This is a test email from WorkMate AI. "
                    "You have my approval to send it."
                )
            )
        ],
        "error": None,
    }

    # STEP 1: Run until the approval interrupt.
    print("\n--- Starting Communication Agent ---")

    result = await graph.ainvoke(initial_state, config=config)

    print("\n--- Approval Required ---")

    interrupts = result.get("__interrupt__", [])

    if not interrupts:
        print("No approval interrupt occurred.")
        print(result)
        return

    for item in interrupts:
        print(item.value)

    # STEP 2: Ask for approval in the terminal.
    decision = input(
        "\nApprove this mock email? Type 'approved' or 'rejected': "
    ).strip().lower()

    while decision not in ("approved", "rejected"):
        decision = input(
            "Please enter 'approved' or 'rejected': "
        ).strip().lower()

    # STEP 3: Resume the graph with the user's decision.
    print("\n--- Resuming Communication Agent ---")

    final_result = await graph.ainvoke(
        Command(resume=decision),
        config=config,
    )

    print("\n--- Final Result ---")

    for message in final_result.get("messages", []):
        print(message)

    print("\nApproval status:", final_result.get("approval_status"))
    print("Error:", final_result.get("error"))


if __name__ == "__main__":
    asyncio.run(main())

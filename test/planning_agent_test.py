import asyncio
from langchain_core.messages import HumanMessage
from langchain_core.tools import tool

from backend.src.agents.planning_agent import (
    build_planning_agent_nodes,
)


# Mock task retrieval tool
@tool
def list_tasks() -> str:
    """Retrieve the user's saved tasks."""
    return """
    [
        {
            "id": 1,
            "title": "Complete WorkMate AI",
            "priority": "high",
            "due_date": "2026-11-05"
        },
        {
            "id": 2,
            "title": "Prepare project documentation",
            "priority": "medium",
            "due_date": "2026-11-07"
        }
    ]
    """


# Mock calendar retrieval tool
@tool
def list_calendar_events() -> str:
    """Retrieve existing Google Calendar events."""
    return """
    [
        {
            "title": "Team Meeting",
            "start": "2026-11-02T10:00:00",
            "end": "2026-11-02T11:00:00"
        }
    ]
    """


async def main():
    # Replace with your actual LLM initialization import.
    from backend.src.assistant.llm import get_llm
    llm = get_llm()

    planning_tools_1 = [
        list_tasks,
        list_calendar_events,
    ]

    # Build Planning Agent and ToolNode.
    planning_agent_node, planning_tools_node = (
        build_planning_agent_nodes(
            llm=llm,
            planning_tools=planning_tools_1,
        )
    )

    # Initial state.
    state = {
        "messages": [
            HumanMessage(
                content=(
                    "Help me plan my work for November 2, 2026. "
                    "Prioritize my high-priority tasks and "
                    "consider my existing calendar events. "
                    "Assume I am available from 9 AM to 5 PM."
                )
            )
        ],
        "error": None,
    }

    # STEP 1: Invoke Planning Agent.
    print("\n--- Planning Agent Response ---")

    result = await planning_agent_node(state)

    ai_message = result["messages"][-1]

    print(ai_message)

    # STEP 2: Check whether tools were requested.
    if ai_message.tool_calls:

        print("\n--- Requested Tool Calls ---")

        for call in ai_message.tool_calls:
            print("Tool:", call["name"])
            print("Arguments:", call["args"])

        # STEP 3: Execute requested tools.
        tool_result = planning_tools_node.invoke(
            {
                "messages": [
                    *state["messages"],
                    ai_message,
                ]
            }
        )

        print("\n--- Tool Execution Results ---")

        for message in tool_result["messages"]:
            print(message.content)

        # STEP 4: Send tool results back to the agent.
        follow_up_state = {
            "messages": [
                *state["messages"],
                ai_message,
                *tool_result["messages"],
            ],
            "error": None,
        }

        final_result = await planning_agent_node(follow_up_state)

        print("\n--- Final Planning Response ---")

        for message in final_result["messages"]:
            print(message.content)

    else:
        print("\nAgent answered without requesting a tool.")


if __name__ == "__main__":
    asyncio.run(main())

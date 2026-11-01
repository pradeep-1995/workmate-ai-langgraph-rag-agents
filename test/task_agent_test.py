# test_task_agent.py

import asyncio

from backend.src.agents.task_agent import build_task_agent
from backend.src.tools.tool_registry import get_agent_tools
from backend.src.assistant.llm import get_llm


async def main():
    llm = get_llm()

    tool_groups = await get_agent_tools()

    task_agent = build_task_agent(
        llm=llm,
        workmate_tools=tool_groups["task"],
    )

    response = await task_agent.ainvoke(
        {
            "messages": [
                (
                    "user",
                    "List my current tasks.",
                )
            ]
        }
    )

    print("\nTask Agent Response:")
    print(response["messages"][-1].content)


if __name__ == "__main__":
    asyncio.run(main())
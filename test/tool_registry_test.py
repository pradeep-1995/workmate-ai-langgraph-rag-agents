
import asyncio

from backend.src.tools.tool_registry import get_agent_tools

"""
TASK AGENT
  - complete_task
  - create_task
  - delete_task
  - list_tasks
  - update_task

RAG AGENT
  - rag_tool

PLANNING AGENT
  - list_tasks
  - create_calendar_event
  - list_calendar_events

COMMUNICATION AGENT
  - create_email_draft
  - read_email
  - search_emails
  - send_email

Tool registry test completed.
"""


async def main():
    agent_tools = await get_agent_tools()

    for agent_name, tools in agent_tools.items():
        print(f"\n{agent_name.upper()} AGENT")

        for tool in tools:
            print(f"  - {tool.name}")

    print("\nTool registry test completed.")


if __name__ == "__main__":
    asyncio.run(main())

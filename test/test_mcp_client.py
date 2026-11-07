import asyncio
from backend.src.mcp.mcp_client import load_workmate_tools, load_calendar_tools, load_gmail_tools
from dotenv import get_key

async def main():
    # Test the local WorkMate MCP server first.
    #tools = await load_workmate_tools()
    tools = await load_gmail_tools()

    print("\n Available MCP tools: ")

    for tool in tools:
        print(f"- {tool.name}: {tool.description}")

if __name__ == "__main__":
    asyncio.run(main())
    
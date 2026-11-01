import asyncio

from backend.src.mcp.mcp_client import load_google_tools


async def main():
    tools = await load_google_tools()

    print("\nAvailable Google MCP tools:")

    for tool in tools:
        print(f"- {tool.name}: {tool.description}")


if __name__ == "__main__":
    asyncio.run(main())
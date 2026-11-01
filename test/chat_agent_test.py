
import asyncio
from langchain_core.messages import HumanMessage
from langchain_core.tools import tool

from backend.src.agents.chat_agent import build_rag_agent_nodes


# Mock retrieval tool
@tool
def search_knowledge_base(query: str) -> str:
    """Search the knowledge base for relevant information."""
    return (
        "WorkMate AI is an AI-powered personal assistant "
        "that manages tasks, retrieves knowledge, and integrates "
        "with Google Workspace."
    )


async def main():
    # Replace this with your actual LLM initialization import.
    from backend.src.assistant.llm import get_llm
    llm = get_llm()

    rag_tools = [search_knowledge_base]

    # Build RAG agent and ToolNode.
    rag_agent_node, rag_tools_node = build_rag_agent_nodes(
        llm=llm,
        rag_tools=rag_tools,
    )

    # Initial conversation state.
    state = {
        "messages": [
            HumanMessage(
                content="What is WorkMate AI and what can it do?"
            )
        ],
        "error": None,
    }

    # STEP 1: Invoke RAG agent.
    print("\n--- RAG Agent Response ---")

    result = await rag_agent_node(state)

    ai_message = result["messages"][-1]

    print(ai_message)

    # STEP 2: Check whether the agent requested a retrieval tool.
    if ai_message.tool_calls:

        print("\n--- Requested Tool Calls ---")

        for call in ai_message.tool_calls:
            print("Tool:", call["name"])
            print("Arguments:", call["args"])

        # STEP 3: Execute retrieval tool.
        tool_result = await rag_tools_node.ainvoke(
            {
                "messages": [
                    *state["messages"],
                    ai_message,
                ]
            }
        )

        print("\n--- Retrieval Results ---")

        for message in tool_result["messages"]:
            print(message.content)

        # STEP 4: Send retrieval results back to the agent.
        follow_up_state = {
            "messages": [
                *state["messages"],
                ai_message,
                *tool_result["messages"],
            ],
            "error": None,
        }

        final_result = await rag_agent_node(follow_up_state)

        print("\n--- Final RAG Answer ---")

        for message in final_result["messages"]:
            print(message.content)

    else:
        print("\nAgent answered without calling a retrieval tool.")


if __name__ == "__main__":
    asyncio.run(main())

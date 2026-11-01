
import asyncio

from langchain_core.messages import HumanMessage

from backend.src.graph.router import (build_router, route_to_agent,)


# Replace this with the same LLM provider/model
# you use in your application.
from backend.src.assistant.llm import get_llm
llm = get_llm()

async def main():
    router_node = build_router(llm)

    test_requests = [
        "Create a task to finish my assignment tomorrow.",
        #"Search my knowledge base for the project notes.",
        "Check my calendar availability for tomorrow.",
        "Draft an email to my manager about the meeting.",
    ]

    for request in test_requests:
        state = {
            "user_request": request,
            "messages": [HumanMessage(content=request)],
            "selected_agent": None,
            "error": None,
        }

        # Test 1: Execute the LLM router node.
        result = await router_node(state)

        print(f"\nRequest: {request}")
        print("Router output:", result)

        # Test 2: Execute the conditional routing function.
        next_agent = route_to_agent({
            **state,
            **result,
        })

        print("Next agent:", next_agent)


if __name__ == "__main__":
    asyncio.run(main())


from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import tools_condition
from langgraph.checkpoint.memory import MemorySaver

from backend.src.graph.state import WorkmateState
from backend.src.graph.router import build_router, route_to_agent

from backend.src.agents.task_agent import build_task_agent_nodes
from backend.src.agents.chat_agent import build_rag_agent_nodes
from backend.src.agents.planning_agent import build_planning_agent_nodes
from backend.src.agents.communication_agent import build_communication_agent_nodes

from backend.core.logging import get_logger
logger = get_logger(__name__)


def build_workmate_graph(llm, 
                         task_tools, 
                         rag_tools, 
                         planning_tools, 
                         communication_tools, 
                         checkpointer = None):

    """
    Build and compile the WorkMate AI LangGraph workflow.

    Args:
        llm: Chat model supporting tool calling.
        task_tools: Task-management MCP tools.
        rag_tools: Knowledge retrieval MCP tools.
        communication_tools: Gmail and Calendar MCP tools.
        checkpointer: Optional LangGraph checkpointer.

    Returns:
        A compiled LangGraph application.
    """
    logger.info("Building WorkMate AI LangGraph workflow.")

    graph = StateGraph(WorkmateState)

    # --------------------------------------------------
    # 1. Router
    # --------------------------------------------------

    router_node = build_router(llm)
    graph.add_node("router", router_node)

    # --------------------------------------------------
    # 2. Task Agent and tools
    # --------------------------------------------------

    task_agent_node, task_tools_node = build_task_agent_nodes(llm, task_tools)

    graph.add_node("task_agent", task_agent_node)
    graph.add_node("task_tool", task_tools_node)

    graph.add_conditional_edges(
        "task_agent",
        tools_condition,
        {
            "tools" : "task_tool",
            END : END,
        },
    )

    graph.add_edge("task_tool", "task_agent")

    # --------------------------------------------------
    # 3. RAG Agent and tools
    # --------------------------------------------------

    rag_agent_node, rag_tools_node = build_rag_agent_nodes(llm, rag_tools)

    graph.add_node("rag_agent", rag_agent_node)
    graph.add_node("rag_tool", rag_tools_node)

    graph.add_conditional_edges(
        "rag_agent",
        tools_condition,
        {
            "tools" : "rag_tool",
            END : END,
        },
    )

    graph.add_edge("rag_tool", "rag_agent")

    # --------------------------------------------------
    # 4. Planning Agent
    # --------------------------------------------------

    planning_agent_node, planning_tools_node = build_planning_agent_nodes(llm, planning_tools)

    graph.add_node("planning_agent", planning_agent_node)
    graph.add_node("planning_tool", planning_tools_node)

    graph.add_conditional_edges(
        "planning_agent",
        tools_condition,
        {
            "tools" : "planning_tool",
            END : END,
        },
    )

    graph.add_edge("planning_tool", "planning_agent")

    # --------------------------------------------------
    # 5. Communication Agent, approval, rejection, and tools
    # --------------------------------------------------
    (
        communication_agent_node, 
        approval_node, 
        communication_rejected_node, 
        communication_tools_node
         ) = build_communication_agent_nodes(
             llm, 
             communication_tools)

    graph.add_node("communication_agent", communication_agent_node)
    graph.add_node("approval", approval_node)
    graph.add_node("communication_rejected", communication_rejected_node)
    graph.add_node("communication_tool", communication_tools_node)

    # If the communication agent requests tools, send them to approval.
    # If it responds directly, end the turn.
    graph.add_conditional_edges(
        "communication_agent",
        tools_condition,
        {
            "tools" : "approval",
            END : END,
        }
    )

    # Approved tool calls execute; rejected calls are cancelled.
    graph.add_conditional_edges(
        "approval",
        lambda state: state.get("approval_status", "rejected"),
        {
            "approved" : "communication_tool",
            "rejected" : "communication_rejected"
        },
    )

    # After approved tools run, return to the agent so it can interpret
    # the tool results and produce the final answer.
    graph.add_edge("communication_tool", "communication_agent")

    # After rejection, return to the agent with ToolMessages so the
    # pending tool calls are properly answered.
    graph.add_edge("communication_rejected", "communication_agent")

    # --------------------------------------------------
    # 6. Entry point and routing
    # --------------------------------------------------

    graph.add_edge(START, "router")

    graph.add_conditional_edges(
        "router",
        route_to_agent,
        {
            "task" : "task_agent",
            "rag" : "rag_agent",
            "planning" : "planning_agent",
            "communication" : "communication_agent",
        },
    )

    # --------------------------------------------------
    # 7. Compile with checkpointer
    # --------------------------------------------------
    if checkpointer is None:
        checkpointer = MemorySaver()

    compiled_graph = graph.compile(checkpointer=checkpointer)
    logger.info("WorkMate AI LangGraph workflow compiled successfully.")

    return compiled_graph


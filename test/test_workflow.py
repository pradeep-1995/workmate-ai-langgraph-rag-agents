import unittest

from langchain_core.tools import tool
from backend.src.graph.workflow import build_workmate_graph


@tool
def stub_tool(query: str) -> str:
    """Return the input unchanged for workflow construction tests."""
    return query


class FakeLLM:
    def bind_tools(self, tools):
        return self

    def with_structured_output(self, schema, **kwargs):
        return self


class WorkflowGraphTests(unittest.TestCase):

    def test_builds_graph_with_all_agent_nodes(self):

        app = build_workmate_graph(
            llm=FakeLLM(),
            task_tools=[stub_tool],
            rag_tools=[stub_tool],
            planning_tools=[stub_tool],
            communication_tools=[stub_tool],
        )

        graph = app.get_graph()

        expected_nodes = {
            "router",
            "task_agent",
            "task_tool",
            "rag_agent",
            "rag_tool",
            "planning_agent",
            "planning_tool",
            "communication_agent",
            "approval",
            "communication_rejected",
            "communication_tool",
        }

        self.assertTrue(expected_nodes.issubset(graph.nodes))

        # Print Mermaid graph
        mermaid = graph.draw_mermaid()

        print("\n========== WORKMATE GRAPH ==========\n")
        print(mermaid)

        # Save Mermaid output
        with open("workmate_graph.md", "w", encoding="utf-8") as f:
            f.write("# WorkMate AI Workflow\n\n")
            f.write("```mermaid\n")
            f.write(mermaid)
            f.write("\n```\n")

        # Save PNG
        png_data = graph.draw_mermaid_png()

        with open("workmate_graph.png", "wb") as f:
            f.write(png_data)

        self.assertIn("task_agent", mermaid)


if __name__ == "__main__":
    unittest.main(verbosity=2)
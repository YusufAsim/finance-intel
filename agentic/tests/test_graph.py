"""Graph shape and end to end flow with mcp stubbed out."""

from langgraph.graph import END, START

from app.graph.build import NODE_NAMES, build_graph
from app.tools.mcp_client import ToolCallError

ACCOUNT = "11111111-2222-3333-4444-555555555555"


def test_graph_holds_the_four_work_nodes_between_start_and_end():
    graph = build_graph()
    nodes = set(graph.get_graph().nodes)
    assert set(NODE_NAMES) <= nodes
    assert {START, END} <= nodes


def test_graph_is_acyclic():
    edges = build_graph().get_graph().edges
    order = [START, "preprocess", "router", "tool_call", "respond", END]
    position = {name: index for index, name in enumerate(order)}
    # every edge moves forward in the pipeline, so no path can loop back
    assert all(position[edge.source] < position[edge.target] for edge in edges)


async def test_flow_answers_from_the_tool_payload(monkeypatch):
    async def fake_call_tool(name, arguments):
        assert name == "get_subscriptions"
        assert arguments == {"account_id": ACCOUNT}
        return {"count": 1, "results": [{"merchant_name": "NETFLIX"}]}

    monkeypatch.setattr("app.graph.nodes.tool_call.call_tool", fake_call_tool)

    state = await build_graph().ainvoke(
        {"question": "aboneliklerim neler", "account_id": ACCOUNT}
    )
    assert state["intent"] == "subscriptions"
    assert state["tool_name"] == "get_subscriptions"
    assert "NETFLIX" in state["answer"]
    assert state.get("error") is None


async def test_flow_reports_an_unreachable_tool(monkeypatch):
    async def fail(name, arguments):
        raise ToolCallError(f"tool {name} could not be called")

    monkeypatch.setattr("app.graph.nodes.tool_call.call_tool", fail)

    state = await build_graph().ainvoke(
        {"question": "aboneliklerim neler", "account_id": ACCOUNT}
    )
    assert state["error"]
    assert state["answer"]


async def test_unknown_question_never_reaches_a_tool(monkeypatch):
    async def fail(name, arguments):  # pragma: no cover - must not run
        raise AssertionError("no tool should be called for an unknown intent")

    monkeypatch.setattr("app.graph.nodes.tool_call.call_tool", fail)

    state = await build_graph().ainvoke(
        {"question": "hava nasıl", "account_id": ACCOUNT}
    )
    assert state["intent"] == "unknown"
    assert state["tool_results"] == {}

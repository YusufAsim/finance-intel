"""Graph wiring.

START -> preprocess -> router -> tool_call -> respond -> END
"""

from functools import lru_cache

from langgraph.graph import END, START, StateGraph

from app.graph.nodes.preprocess import preprocess
from app.graph.nodes.respond import respond
from app.graph.nodes.route import route
from app.graph.nodes.tool_call import tool_call
from app.graph.state import AgentState

NODE_NAMES = ("preprocess", "router", "tool_call", "respond")


def build_graph():
    graph = StateGraph(AgentState)
    graph.add_node("preprocess", preprocess)
    graph.add_node("router", route)
    graph.add_node("tool_call", tool_call)
    graph.add_node("respond", respond)

    graph.add_edge(START, "preprocess")
    graph.add_edge("preprocess", "router")
    graph.add_edge("router", "tool_call")
    graph.add_edge("tool_call", "respond")
    graph.add_edge("respond", END)

    return graph.compile()


@lru_cache
def get_graph():
    """The compiled graph is stateless, so one instance is enough."""
    return build_graph()

"""State carried through the graph."""

from typing import Any, TypedDict


class AgentState(TypedDict, total=False):
    """One pass through the graph, from question to answer."""

    question: str
    account_id: str | None
    # normalised form of the question, filled in by preprocess
    normalized: str
    intent: str
    tool_name: str | None
    tool_args: dict[str, Any]
    tool_results: dict[str, Any]
    answer: str
    error: str | None

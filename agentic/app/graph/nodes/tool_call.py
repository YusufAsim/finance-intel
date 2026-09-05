"""Tool execution."""

from app.graph.state import AgentState
from app.tools.mcp_client import ToolCallError, call_tool


async def tool_call(state: AgentState) -> AgentState:
    """Run the tool the router picked, if there is one."""
    tool_name = state.get("tool_name")
    if not tool_name:
        return {**state, "tool_results": {}}

    try:
        payload = await call_tool(tool_name, state.get("tool_args", {}))
    except ToolCallError as exc:
        return {**state, "tool_results": {}, "error": str(exc)}

    error = payload.get("error") if isinstance(payload, dict) else None
    return {**state, "tool_results": payload, "error": error}

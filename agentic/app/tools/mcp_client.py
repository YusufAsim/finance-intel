"""Access to the mcp tool surface.

This is the only door out of the agentic service. Backend and ml are
never called directly.
"""

import json
import logging
from typing import Any

from fastmcp import Client

from app.config import get_settings

logger = logging.getLogger(__name__)


class ToolCallError(RuntimeError):
    """Raised when a tool cannot be reached or refuses the call."""


def _endpoint() -> str:
    return f"{get_settings().mcp_base_url.rstrip('/')}/mcp/"


def _unwrap(result: Any) -> dict:
    """Turn an mcp result into the plain payload the tool returned."""
    data = getattr(result, "data", None)
    if isinstance(data, dict):
        return data

    structured = getattr(result, "structured_content", None)
    if isinstance(structured, dict):
        return structured.get("result", structured)

    content = getattr(result, "content", None) or []
    for block in content:
        text = getattr(block, "text", None)
        if text:
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                return {"text": text}
    return {}


async def call_tool(name: str, arguments: dict[str, Any]) -> dict:
    """Call one mcp tool and return its payload."""
    cleaned = {key: value for key, value in arguments.items() if value is not None}
    try:
        async with Client(_endpoint()) as client:
            result = await client.call_tool(name, cleaned)
    except Exception as exc:  # noqa: BLE001 - reported to the caller as one error
        logger.warning("tool %s failed: %s", name, exc)
        raise ToolCallError(f"tool {name} could not be called") from exc
    return _unwrap(result)


async def list_tools() -> list[str]:
    """Names of the tools the mcp service currently exposes."""
    try:
        async with Client(_endpoint()) as client:
            return [tool.name for tool in await client.list_tools()]
    except Exception as exc:  # noqa: BLE001 - reported to the caller as one error
        raise ToolCallError("mcp service is unreachable") from exc

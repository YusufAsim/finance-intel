"""Health route and tool registration."""

from fastapi.testclient import TestClient

from app.server import app
from app.tools.finance import mcp

EXPECTED_TOOLS = {
    "get_transactions",
    "get_account_summary",
    "get_subscriptions",
    "get_anomalies",
    "get_forecast",
    "search_merchants",
    "list_accounts",
}


def test_healthz_answers_without_touching_the_backend():
    with TestClient(app) as client:
        response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_every_tool_is_registered():
    names = {tool.name for tool in await mcp.list_tools()}
    assert EXPECTED_TOOLS <= names


async def test_every_tool_describes_itself():
    for tool in await mcp.list_tools():
        # the description is what the model reads to decide on a call
        assert tool.description and len(tool.description.strip()) > 20

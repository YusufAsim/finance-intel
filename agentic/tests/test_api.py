"""HTTP surface of the agentic service."""

import pytest
from fastapi.testclient import TestClient

from app.main import app

ACCOUNT = "11111111-2222-3333-4444-555555555555"


@pytest.fixture
def client():
    return TestClient(app)


def test_healthz_needs_no_provider(client):
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_chat_returns_the_routed_answer(client, monkeypatch):
    async def fake_call_tool(name, arguments):
        return {"count": 1, "results": [{"name": "employee account", "id": ACCOUNT}]}

    monkeypatch.setattr("app.graph.nodes.tool_call.call_tool", fake_call_tool)

    response = client.post(
        "/chat", json={"question": "hesaplarım neler", "account_id": ACCOUNT}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["intent"] == "accounts"
    assert body["tool_name"] == "list_accounts"
    assert "employee account" in body["answer"]


def test_chat_rejects_an_empty_question(client):
    assert client.post("/chat", json={"question": ""}).status_code == 422

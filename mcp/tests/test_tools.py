"""Tool behaviour with the backend client stubbed out."""

import pytest

from app.clients.backend import UpstreamError
from app.tools import finance

ACCOUNT = "11111111-2222-3333-4444-555555555555"


class StubClient:
    """Records the call and returns a canned payload."""

    def __init__(self, payload=None, error=None):
        self.payload = payload if payload is not None else {"count": 0, "results": []}
        self.error = error
        self.calls = []

    def __getattr__(self, name):
        async def call(**params):
            self.calls.append((name, params))
            if self.error:
                raise self.error
            return self.payload

        return call


@pytest.fixture
def stub(monkeypatch):
    client = StubClient()
    monkeypatch.setattr(finance, "_client", lambda: client)
    return client


async def test_get_transactions_passes_the_filters(stub):
    stub.payload = {"count": 1, "results": [{"id": "1"}]}
    result = await finance.get_transactions(account_id=ACCOUNT, category="groceries")
    assert result["count"] == 1
    name, params = stub.calls[0]
    assert params["account"] == ACCOUNT
    assert params["category"] == "groceries"


async def test_get_transactions_caps_the_limit(stub):
    await finance.get_transactions(account_id=ACCOUNT, limit=10_000)
    _, params = stub.calls[0]
    assert params["page_size"] <= finance.MAX_LIMIT


async def test_upstream_failure_becomes_a_readable_payload(monkeypatch):
    client = StubClient(error=UpstreamError("backend is unreachable"))
    monkeypatch.setattr(finance, "_client", lambda: client)

    result = await finance.get_transactions(account_id=ACCOUNT)
    assert result["error"] == "backend is unreachable"
    assert result["results"] == []
    assert result["count"] == 0


async def test_list_accounts_needs_no_arguments(stub):
    stub.payload = {"count": 2, "results": [{"id": ACCOUNT}]}
    result = await finance.list_accounts()
    assert result["count"] == 2

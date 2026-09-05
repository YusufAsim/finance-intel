"""Keyword routing."""

import pytest

from app.graph.nodes.preprocess import preprocess
from app.graph.nodes.route import route

ACCOUNT = "11111111-2222-3333-4444-555555555555"


def _intent(question: str, account_id: str | None = ACCOUNT) -> str:
    state = preprocess({"question": question, "account_id": account_id})
    return route(state)["intent"]


@pytest.mark.parametrize(
    ("question", "expected"),
    [
        ("aboneliklerim neler", "subscriptions"),
        ("which subscriptions do i pay", "subscriptions"),
        ("garip bir harcama var mı", "anomalies"),
        ("anything suspicious this month", "anomalies"),
        ("önümüzdeki ay tahmini nedir", "forecast"),
        ("what is the forecast", "forecast"),
        ("geçen ay ne kadar harcadım", "summary"),
        ("give me a category breakdown", "summary"),
        ("son işlemlerimi göster", "transactions"),
        ("show my recent transactions", "transactions"),
        ("hesaplarım neler", "accounts"),
        ("hava nasıl", "unknown"),
    ],
)
def test_question_maps_to_intent(question, expected):
    assert _intent(question) == expected


def test_unknown_intent_selects_no_tool():
    state = route(preprocess({"question": "hava nasıl", "account_id": ACCOUNT}))
    assert state["tool_name"] is None


def test_account_scoped_question_without_an_account_falls_back():
    state = route(preprocess({"question": "aboneliklerim neler", "account_id": None}))
    assert state["intent"] == "accounts"
    assert state["tool_name"] == "list_accounts"


def test_transactions_intent_carries_a_limit():
    state = route(preprocess({"question": "son işlemlerim", "account_id": ACCOUNT}))
    assert state["tool_args"] == {"account_id": ACCOUNT, "limit": 20}


def test_account_scoped_intent_passes_the_account():
    state = route(preprocess({"question": "aboneliklerim", "account_id": ACCOUNT}))
    assert state["tool_args"] == {"account_id": ACCOUNT}

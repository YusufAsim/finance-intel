"""Answer assembly.

Answers are templated from the tool payload. A model based writer would
replace this node without touching the rest of the graph.
"""

from app.graph.nodes.route import (
    INTENT_ACCOUNTS,
    INTENT_ANOMALIES,
    INTENT_FORECAST,
    INTENT_SUBSCRIPTIONS,
    INTENT_SUMMARY,
    INTENT_TRANSACTIONS,
)
from app.graph.state import AgentState

FALLBACK = (
    "I could not tell what this question is about. Try asking about "
    "transactions, subscriptions, anomalies, totals or a forecast."
)


def respond(state: AgentState) -> AgentState:
    """Turn the tool payload into a sentence."""
    if state.get("error"):
        return {**state, "answer": f"The data could not be fetched: {state['error']}"}

    results = state.get("tool_results") or {}
    intent = state.get("intent")

    if intent == INTENT_SUBSCRIPTIONS:
        answer = _subscriptions(results)
    elif intent == INTENT_ANOMALIES:
        answer = _anomalies(results)
    elif intent == INTENT_FORECAST:
        answer = _forecast(results)
    elif intent == INTENT_SUMMARY:
        answer = _summary(results)
    elif intent == INTENT_TRANSACTIONS:
        answer = _transactions(results)
    elif intent == INTENT_ACCOUNTS:
        answer = _accounts(results)
    else:
        answer = FALLBACK

    return {**state, "answer": answer}


def _subscriptions(results: dict) -> str:
    rows = results.get("results", [])
    if not rows:
        return "No recurring charges were found on this account."
    names = ", ".join(row.get("merchant_name", "unknown") for row in rows[:5])
    return f"{len(rows)} recurring charges were found: {names}."


def _anomalies(results: dict) -> str:
    rows = results.get("results", [])
    if not rows:
        return "Nothing on this account looks unusual."
    kinds = sorted({row.get("kind", "unknown") for row in rows})
    return f"{len(rows)} transactions were flagged, covering {', '.join(kinds)}."


def _forecast(results: dict) -> str:
    points = results.get("points", [])
    if not points:
        return "No projection could be produced for this account."
    last = points[-1]
    return (
        f"Over the next {results.get('horizon_days', len(points))} days the balance "
        f"is projected to reach {last.get('expected_balance')}."
    )


def _summary(results: dict) -> str:
    if not results or "total_expense" not in results:
        return "No totals are available for this account."
    categories = results.get("categories", [])
    top = categories[0]["category"] if categories else "nothing"
    return (
        f"Income totals {results.get('total_income')} against "
        f"{results.get('total_expense')} of spending, and the largest "
        f"category is {top}."
    )


def _transactions(results: dict) -> str:
    rows = results.get("results", [])
    if not rows:
        return "No transactions matched that question."
    return (
        f"{results.get('count', len(rows))} transactions matched, the most recent "
        f"is {rows[0].get('raw_description')} for {rows[0].get('amount')}."
    )


def _accounts(results: dict) -> str:
    rows = results.get("results", [])
    if not rows:
        return "There are no accounts on the platform yet."
    names = ", ".join(f"{row.get('name')} ({row.get('id')})" for row in rows)
    return f"{len(rows)} accounts are available: {names}."

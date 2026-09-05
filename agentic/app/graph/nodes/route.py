"""Intent routing.

Rule based on purpose: the routing decision is a keyword match today, so
the graph can be exercised without a model provider. Swapping in a model
means replacing this node, nothing else.
"""

from app.graph.state import AgentState

INTENT_SUBSCRIPTIONS = "subscriptions"
INTENT_ANOMALIES = "anomalies"
INTENT_FORECAST = "forecast"
INTENT_SUMMARY = "summary"
INTENT_TRANSACTIONS = "transactions"
INTENT_ACCOUNTS = "accounts"
INTENT_UNKNOWN = "unknown"

# Checked in order, first hit wins. Turkish entries are stems rather than
# whole words, because the suffixes vary: "abone" covers aboneligim and
# aboneliklerim alike.
RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        INTENT_SUBSCRIPTIONS,
        ("subscription", "abone", "recurring", "membership", "uyelik", "duzenli"),
    ),
    (
        INTENT_ANOMALIES,
        (
            "anomaly",
            "anomali",
            "unusual",
            "suspicious",
            "strange",
            "duplicate",
            "garip",
            "tuhaf",
            "olagandisi",
            "supheli",
        ),
    ),
    (
        INTENT_FORECAST,
        ("forecast", "projection", "tahmin", "future", "next month", "run out"),
    ),
    (
        INTENT_SUMMARY,
        (
            "summary",
            "ozet",
            "total",
            "toplam",
            "how much",
            "ne kadar",
            "breakdown",
            "category",
            "kategori",
            "dagilim",
        ),
    ),
    (
        INTENT_TRANSACTIONS,
        (
            "transaction",
            "islem",
            "spend",
            "harca",
            "payment",
            "odeme",
            "charge",
            "bought",
        ),
    ),
    (INTENT_ACCOUNTS, ("account", "hesap", "which accounts")),
)

TOOL_BY_INTENT = {
    INTENT_SUBSCRIPTIONS: "get_subscriptions",
    INTENT_ANOMALIES: "get_anomalies",
    INTENT_FORECAST: "get_forecast",
    INTENT_SUMMARY: "get_account_summary",
    INTENT_TRANSACTIONS: "get_transactions",
    INTENT_ACCOUNTS: "list_accounts",
    INTENT_UNKNOWN: None,
}


def classify(normalized: str) -> str:
    for intent, keywords in RULES:
        if any(keyword in normalized for keyword in keywords):
            return intent
    return INTENT_UNKNOWN


def route(state: AgentState) -> AgentState:
    """Pick an intent and the tool that answers it."""
    intent = classify(state.get("normalized", ""))
    tool_name = TOOL_BY_INTENT[intent]

    account_id = state.get("account_id")
    if tool_name and tool_name != "list_accounts" and not account_id:
        # nothing can be answered per account without an account
        tool_name = "list_accounts"
        intent = INTENT_ACCOUNTS

    arguments: dict = {}
    if tool_name in {
        "get_subscriptions",
        "get_anomalies",
        "get_account_summary",
        "get_forecast",
    }:
        arguments["account_id"] = account_id
    elif tool_name == "get_transactions":
        arguments["account_id"] = account_id
        arguments["limit"] = 20

    return {**state, "intent": intent, "tool_name": tool_name, "tool_args": arguments}

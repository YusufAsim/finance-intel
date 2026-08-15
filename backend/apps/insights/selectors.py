"""Read side queries backing the account insight endpoints."""

from decimal import Decimal

from django.db.models import Count, Max, Min, Q, Sum

from apps.accounts.models import Account
from apps.transactions.models import AnomalyFlag, Subscription, Transaction

ZERO = Decimal("0.00")


def period_bounds(account: Account) -> tuple[str | None, str | None]:
    rows = Transaction.objects.filter(account=account).aggregate(
        first=Min("date"), last=Max("date")
    )
    return rows["first"], rows["last"]


def account_summary(account: Account) -> dict:
    """Totals and per category breakdown for one account."""
    queryset = Transaction.objects.filter(account=account)

    totals = queryset.aggregate(
        income=Sum("amount", filter=Q(direction=Transaction.Direction.IN)),
        expense=Sum("amount", filter=Q(direction=Transaction.Direction.OUT)),
        count=Count("id"),
    )
    income = totals["income"] or ZERO
    expense = totals["expense"] or ZERO

    breakdown = (
        queryset.filter(direction=Transaction.Direction.OUT)
        .values("category__slug")
        .annotate(total=Sum("amount"), count=Count("id"))
        .order_by("-total")
    )

    first, last = period_bounds(account)

    categories = []
    for row in breakdown:
        total = row["total"] or ZERO
        share = (total / expense) if expense else ZERO
        categories.append(
            {
                "category": row["category__slug"] or "uncategorized",
                "total": _money(total),
                "count": row["count"],
                "share": float(round(share, 4)),
            }
        )

    return {
        "account_id": str(account.id),
        "period": {"start": first, "end": last},
        "transaction_count": totals["count"],
        "total_income": _money(income),
        "total_expense": _money(expense),
        "net": _money(income - expense),
        "categories": categories,
    }


def _money(value: Decimal) -> str:
    """Money is rendered as a string so no precision is lost on the wire."""
    return f"{value.quantize(Decimal('0.01'))}"


def account_subscriptions(account: Account):
    return (
        Subscription.objects.filter(account=account)
        .select_related("merchant")
        .order_by("merchant__name")
    )


def account_anomalies(account: Account):
    return (
        AnomalyFlag.objects.filter(transaction__account=account)
        .select_related("transaction")
        .order_by("-transaction__date")
    )


def forecast_history(account: Account, days: int = 400) -> list[dict]:
    """Recent movements handed to the ml service as forecast input."""
    rows = (
        Transaction.objects.filter(account=account)
        .order_by("-date")[:2000]
        .values("date", "amount", "direction", "raw_description")
    )
    return [
        {
            "date": row["date"].isoformat(),
            "amount": str(row["amount"]),
            "direction": row["direction"],
            "raw_description": row["raw_description"],
        }
        for row in reversed(list(rows))
    ]

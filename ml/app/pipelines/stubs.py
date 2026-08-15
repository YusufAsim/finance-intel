"""Placeholder logic behind the endpoints.

Nothing here is a trained model. Each function returns a fixed but
plausible answer so the rest of the platform can be built and tested
against the real response shape.
"""

import hashlib
import re
from collections import defaultdict
from datetime import timedelta
from decimal import Decimal

from app.schemas import TransactionIn

MODEL_VERSION = "stub-0.1.0"

# Keyword hints used to pick a plausible category for a description.
_KEYWORDS = {
    "salary": ("MAAS", "HAVALE"),
    "rent": ("KIRA",),
    "subscription": ("SPOTIFY", "NETFLIX", "ADOBE", "FIGMA", "ICLOUD", "YOUTUBE"),
    "utilities": ("ENERJISA", "BASKENTGAZ", "ASKI", "SUPERONLINE"),
    "groceries": ("MIGROS", "SOK", "BIM", "CARREFOUR", "A101"),
    "dining": ("STARBUCKS", "KAHVE", "BURGER", "SIMIT", "DOMINOS"),
    "electronics": ("MEDIAMARKT", "TEKNOSA", "VATAN"),
    "travel": ("THY", "PEGASUS", "BOOKING"),
    "health": ("HASTANE", "ECZANE", "LABORATUVAR"),
}

_TERMINAL = re.compile(r"\s\d{3,}$")


def merchant_of(raw_description: str) -> str:
    """Drop the trailing terminal number from a card description."""
    return _TERMINAL.sub("", raw_description).strip()


def _stable_unit(value: str) -> float:
    """Map a string to a stable number in [0, 1).

    Used so a stub answer looks varied while staying reproducible.
    """
    digest = hashlib.sha256(value.encode("utf-8")).digest()
    return int.from_bytes(digest[:4], "big") / 2**32


def guess_category(raw_description: str) -> tuple[str, float]:
    upper = raw_description.upper()
    for category, hints in _KEYWORDS.items():
        if any(hint in upper for hint in hints):
            return category, round(0.82 + _stable_unit(upper) * 0.17, 4)
    return "other", round(0.35 + _stable_unit(upper) * 0.2, 4)


def categorize(transactions: list[TransactionIn]) -> tuple[list[dict], float]:
    predictions = []
    for item in transactions:
        category, confidence = guess_category(item.raw_description)
        predictions.append(
            {
                "transaction_id": item.id,
                "category": category,
                "confidence": confidence,
            }
        )
    overall = sum(row["confidence"] for row in predictions) / len(predictions)
    return predictions, round(overall, 4)


def recurring(transactions: list[TransactionIn]) -> tuple[list[dict], float]:
    """Group by merchant and keep the groups that repeat monthly."""
    grouped: dict[str, list[TransactionIn]] = defaultdict(list)
    for item in transactions:
        grouped[merchant_of(item.raw_description)].append(item)

    series = []
    for merchant, items in sorted(grouped.items()):
        if len(items) < 3:
            continue
        ordered = sorted(items, key=lambda row: row.date)
        months = {(row.date.year, row.date.month) for row in ordered}
        if len(months) < 3:
            continue
        total = sum((row.amount for row in ordered), Decimal("0"))
        average = (total / len(ordered)).quantize(Decimal("0.01"))
        last = ordered[-1].date
        series.append(
            {
                "series_id": hashlib.sha256(merchant.encode("utf-8")).hexdigest()[:32],
                "merchant": merchant,
                "cadence": "monthly",
                "average_amount": average,
                "occurrences": len(ordered),
                "transaction_ids": [row.id for row in ordered if row.id],
                "next_expected_date": last + timedelta(days=30),
                "confidence": round(0.7 + _stable_unit(merchant) * 0.29, 4),
            }
        )
    overall = (
        round(sum(row["confidence"] for row in series) / len(series), 4)
        if series
        else 0.0
    )
    return series, overall


def _median(amounts: list[Decimal]) -> Decimal:
    ordered = sorted(amounts)
    middle = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[middle]
    return (ordered[middle - 1] + ordered[middle]) / 2


def anomaly(transactions: list[TransactionIn]) -> tuple[list[dict], float]:
    """Score against the median amount of the same merchant."""
    by_merchant: dict[str, list[Decimal]] = defaultdict(list)
    for item in transactions:
        by_merchant[merchant_of(item.raw_description)].append(item.amount)

    typical = {merchant: _median(amounts) for merchant, amounts in by_merchant.items()}

    scores = []
    for item in transactions:
        merchant = merchant_of(item.raw_description)
        baseline = typical[merchant] or Decimal("1")
        ratio = float(item.amount / baseline)
        score = min(0.99, max(0.01, (ratio - 1) / 8))
        flagged = ratio >= 4
        scores.append(
            {
                "transaction_id": item.id,
                "score": round(score, 4),
                "kind": "amount_spike" if flagged else None,
                "is_anomaly": flagged,
            }
        )
    overall = round(sum(row["score"] for row in scores) / len(scores), 4)
    return scores, min(0.99, max(0.01, overall))


def forecast(
    transactions: list[TransactionIn], horizon_days: int
) -> tuple[list[dict], float]:
    """Project the daily average forward from the last known balance."""
    ordered = sorted(transactions, key=lambda row: row.date)
    first, last = ordered[0].date, ordered[-1].date
    span_days = max((last - first).days, 1)

    income = sum((row.amount for row in ordered if row.direction == "in"), Decimal("0"))
    expense = sum(
        (row.amount for row in ordered if row.direction == "out"), Decimal("0")
    )

    daily_income = (income / span_days).quantize(Decimal("0.01"))
    daily_expense = (expense / span_days).quantize(Decimal("0.01"))
    balance = (income - expense).quantize(Decimal("0.01"))

    points = []
    for offset in range(1, horizon_days + 1):
        balance = (balance + daily_income - daily_expense).quantize(Decimal("0.01"))
        points.append(
            {
                "date": last + timedelta(days=offset),
                "expected_balance": balance,
                "expected_income": daily_income,
                "expected_expense": daily_expense,
            }
        )

    # confidence drops as the horizon stretches further out
    confidence = round(max(0.35, 0.9 - horizon_days / 1000), 4)
    return points, confidence

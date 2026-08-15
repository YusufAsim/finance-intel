"""Data structures shared across the generator."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

# Direction of money movement as seen from the account holder.
INCOMING = "in"
OUTGOING = "out"

CATEGORY_SALARY = "salary"
CATEGORY_RENT = "rent"
CATEGORY_SUBSCRIPTION = "subscription"
CATEGORY_UTILITIES = "utilities"
CATEGORY_GROCERIES = "groceries"
CATEGORY_DINING = "dining"
CATEGORY_ELECTRONICS = "electronics"
CATEGORY_TRAVEL = "travel"
CATEGORY_HEALTH = "health"
CATEGORY_OTHER = "other"

ANOMALY_AMOUNT_SPIKE = "amount_spike"
ANOMALY_DUPLICATE = "duplicate"
ANOMALY_UNUSUAL_MERCHANT = "unusual_merchant"
ANOMALY_OFF_SCHEDULE = "off_schedule"


@dataclass(frozen=True)
class DraftTransaction:
    """A transaction before ordering, identity and balance are assigned.

    ``order`` keeps generation order so that sorting stays stable when
    several transactions land on the same day.
    """

    order: int
    booked_on: date
    amount: Decimal
    direction: str
    raw_description: str
    category: str
    series_key: str | None = None
    anomaly_kind: str | None = None


@dataclass(frozen=True)
class Statement:
    """Finished output: the statement itself plus its ground truth."""

    transactions: list[dict]
    labels: list[dict]

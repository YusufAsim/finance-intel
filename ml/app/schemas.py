"""Request and response models.

These schemas are the contract the rest of the platform codes against.
They stay the same when the stubs are replaced by trained models.
"""

from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field

Direction = Literal["in", "out"]

CATEGORIES = (
    "salary",
    "rent",
    "subscription",
    "utilities",
    "groceries",
    "dining",
    "electronics",
    "travel",
    "health",
    "other",
)

AnomalyKind = Literal["amount_spike", "duplicate", "unusual_merchant", "off_schedule"]


class TransactionIn(BaseModel):
    """One movement as the rest of the platform passes it around."""

    id: str | None = None
    date: date
    amount: Decimal = Field(gt=0)
    direction: Direction
    raw_description: str = Field(min_length=1, max_length=255)


class TransactionBatch(BaseModel):
    transactions: list[TransactionIn] = Field(min_length=1)


class CategoryPrediction(BaseModel):
    transaction_id: str | None
    category: str
    confidence: float = Field(ge=0, le=1)


class CategorizeResponse(BaseModel):
    model_version: str
    predictions: list[CategoryPrediction]
    confidence: float = Field(ge=0, le=1)


class RecurringSeries(BaseModel):
    series_id: str
    merchant: str
    cadence: Literal["monthly", "yearly"]
    average_amount: Decimal
    occurrences: int
    transaction_ids: list[str]
    next_expected_date: date | None = None
    confidence: float = Field(ge=0, le=1)


class RecurringResponse(BaseModel):
    model_version: str
    series: list[RecurringSeries]
    confidence: float = Field(ge=0, le=1)


class AnomalyScore(BaseModel):
    transaction_id: str | None
    score: float = Field(ge=0, le=1)
    kind: AnomalyKind | None = None
    is_anomaly: bool


class AnomalyResponse(BaseModel):
    model_version: str
    scores: list[AnomalyScore]
    confidence: float = Field(ge=0, le=1)


class ForecastRequest(TransactionBatch):
    horizon_days: int = Field(default=30, ge=1, le=365)


class ForecastPoint(BaseModel):
    date: date
    expected_balance: Decimal
    expected_income: Decimal
    expected_expense: Decimal


class ForecastResponse(BaseModel):
    model_version: str
    horizon_days: int
    points: list[ForecastPoint]
    confidence: float = Field(ge=0, le=1)

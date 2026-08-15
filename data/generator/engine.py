"""Statement generation.

Everything random goes through a single ``Random`` instance seeded by the
caller, and the order of generation is fixed, so the same seed always
produces the same statement down to the byte.
"""

import calendar
import uuid
from dataclasses import replace
from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal
from random import Random

from generator import merchants
from generator.models import (
    ANOMALY_AMOUNT_SPIKE,
    ANOMALY_DUPLICATE,
    ANOMALY_OFF_SCHEDULE,
    ANOMALY_UNUSUAL_MERCHANT,
    CATEGORY_DINING,
    CATEGORY_ELECTRONICS,
    CATEGORY_GROCERIES,
    CATEGORY_HEALTH,
    CATEGORY_OTHER,
    CATEGORY_RENT,
    CATEGORY_SALARY,
    CATEGORY_SUBSCRIPTION,
    CATEGORY_TRAVEL,
    CATEGORY_UTILITIES,
    INCOMING,
    OUTGOING,
    DraftTransaction,
    Statement,
)
from generator.profiles import Profile

# Statements start here regardless of the current date, so output does not
# drift as time passes.
DEFAULT_START = date(2024, 1, 1)

# Share of transactions that are deliberately planted as anomalies.
ANOMALY_RATE = Decimal("0.02")

CENT = Decimal("0.01")

_NAMESPACE = uuid.UUID("6f1a0f7c-6f4c-5f2a-9c4d-1c2b3a4d5e6f")

# Months where heating and lighting bills climb.
_COLD_MONTHS = {12, 1, 2}
_SHOULDER_MONTHS = {11, 3}


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


def _money_between(rng: Random, low: Decimal, high: Decimal) -> Decimal:
    """Draw an amount in cents so results stay exact."""
    low_cents = int(low * 100)
    high_cents = int(high * 100)
    if high_cents < low_cents:
        low_cents, high_cents = high_cents, low_cents
    return Decimal(rng.randint(low_cents, high_cents)) / 100


def _clamp_day(year: int, month: int, day: int) -> date:
    last = calendar.monthrange(year, month)[1]
    return date(year, month, min(max(day, 1), last))


def _months(start: date, count: int) -> list[tuple[int, int]]:
    result = []
    year, month = start.year, start.month
    for _ in range(count):
        result.append((year, month))
        month += 1
        if month > 12:
            month = 1
            year += 1
    return result


def _seasonal_factor(month: int) -> Decimal:
    if month in _COLD_MONTHS:
        return Decimal("1.0")
    if month in _SHOULDER_MONTHS:
        return Decimal("0.7")
    return Decimal("0.25")


def _series_id(profile: str, seed: int, key: str) -> str:
    return str(uuid.uuid5(_NAMESPACE, f"series/{profile}/{seed}/{key}"))


def _transaction_id(profile: str, seed: int, index: int) -> str:
    return str(uuid.uuid5(_NAMESPACE, f"transaction/{profile}/{seed}/{index}"))


class _Builder:
    """Collects drafts while keeping a stable generation order."""

    def __init__(self) -> None:
        self._drafts: list[DraftTransaction] = []

    def add(self, **kwargs) -> None:
        self._drafts.append(DraftTransaction(order=len(self._drafts), **kwargs))

    @property
    def drafts(self) -> list[DraftTransaction]:
        return self._drafts


def _add_income(
    builder: _Builder, rng: Random, profile: Profile, months: list[tuple[int, int]]
) -> None:
    for stream in profile.incomes:
        # a single raise lands somewhere in the second half of the history
        raise_at = rng.randint(len(months) // 2, len(months) - 1)
        raise_factor = Decimal("1.00") + Decimal(rng.randint(6, 14)) / 100
        for position, (year, month) in enumerate(months):
            payments = rng.randint(*stream.per_month)
            for payment in range(payments):
                jitter = rng.randint(-stream.day_jitter, stream.day_jitter)
                booked_on = _clamp_day(year, month, stream.day + jitter + payment * 7)
                amount = _money_between(rng, stream.amount_low, stream.amount_high)
                if position >= raise_at:
                    amount = _quantize(amount * raise_factor)
                builder.add(
                    booked_on=booked_on,
                    amount=amount,
                    direction=INCOMING,
                    raw_description=stream.description,
                    category=CATEGORY_SALARY,
                    series_key=f"income:{stream.name}",
                )


def _add_rent(
    builder: _Builder, profile: Profile, months: list[tuple[int, int]]
) -> None:
    if profile.rent_day is None or profile.rent_amount is None:
        return
    for year, month in months:
        builder.add(
            booked_on=_clamp_day(year, month, profile.rent_day),
            amount=profile.rent_amount,
            direction=OUTGOING,
            raw_description="KIRA ODEMESI EFT",
            category=CATEGORY_RENT,
            series_key="rent",
        )


def _add_subscriptions(
    builder: _Builder, rng: Random, profile: Profile, months: list[tuple[int, int]]
) -> None:
    for subscription in profile.subscriptions:
        # one or two price rises spread over the whole history
        rise_count = rng.randint(1, 2)
        rise_points = sorted(
            rng.sample(range(3, len(months)), rise_count) if len(months) > 4 else []
        )
        amount = subscription.amount
        for position, (year, month) in enumerate(months):
            if position in rise_points:
                amount = _quantize(
                    amount * (Decimal("1.00") + Decimal(rng.randint(8, 25)) / 100)
                )
            builder.add(
                booked_on=_clamp_day(year, month, subscription.day),
                amount=amount,
                direction=OUTGOING,
                raw_description=subscription.description,
                category=CATEGORY_SUBSCRIPTION,
                series_key=f"subscription:{subscription.name}",
            )


def _add_utilities(
    builder: _Builder, rng: Random, profile: Profile, months: list[tuple[int, int]]
) -> None:
    for utility in profile.utilities:
        for year, month in months:
            if utility.seasonal:
                span = utility.amount_high - utility.amount_low
                base = utility.amount_low + span * _seasonal_factor(month)
                low = base * Decimal("0.92")
                high = base * Decimal("1.08")
                amount = _quantize(_money_between(rng, low, high))
            else:
                amount = _money_between(rng, utility.amount_low, utility.amount_high)
            builder.add(
                booked_on=_clamp_day(year, month, utility.day),
                amount=amount,
                direction=OUTGOING,
                raw_description=utility.description,
                category=CATEGORY_UTILITIES,
                series_key=f"utility:{utility.name}",
            )


def _add_groceries(
    builder: _Builder,
    rng: Random,
    profile: Profile,
    start: date,
    months: list[tuple[int, int]],
) -> None:
    last_year, last_month = months[-1]
    end = _clamp_day(last_year, last_month, 28)
    week_start = start
    while week_start <= end:
        visits = rng.randint(*profile.grocery_visits_per_week)
        for _ in range(visits):
            offset = rng.randint(0, 6)
            booked_on = week_start + timedelta(days=offset)
            if booked_on > end:
                continue
            builder.add(
                booked_on=booked_on,
                amount=_money_between(rng, *profile.grocery_amount),
                direction=OUTGOING,
                raw_description=merchants.pick(rng, merchants.GROCERY_MERCHANTS),
                category=CATEGORY_GROCERIES,
            )
        week_start += timedelta(days=7)


def _add_dining(
    builder: _Builder, rng: Random, profile: Profile, months: list[tuple[int, int]]
) -> None:
    for year, month in months:
        last_day = calendar.monthrange(year, month)[1]
        for _ in range(rng.randint(*profile.dining_per_month)):
            builder.add(
                booked_on=date(year, month, rng.randint(1, last_day)),
                amount=_money_between(rng, *profile.dining_amount),
                direction=OUTGOING,
                raw_description=merchants.pick(rng, merchants.DINING_MERCHANTS),
                category=CATEGORY_DINING,
            )


def _add_big_purchases(
    builder: _Builder, rng: Random, profile: Profile, months: list[tuple[int, int]]
) -> None:
    total = max(1, round(profile.big_purchases_per_year * len(months) / 12))
    options = (
        (
            CATEGORY_ELECTRONICS,
            merchants.ELECTRONICS_MERCHANTS,
            Decimal("4500.00"),
            Decimal("52000.00"),
        ),
        (
            CATEGORY_TRAVEL,
            merchants.TRAVEL_MERCHANTS,
            Decimal("6000.00"),
            Decimal("38000.00"),
        ),
        (
            CATEGORY_HEALTH,
            merchants.HEALTH_MERCHANTS,
            Decimal("900.00"),
            Decimal("14000.00"),
        ),
    )
    for _ in range(total):
        year, month = months[rng.randint(0, len(months) - 1)]
        category, pool, low, high = options[rng.randint(0, len(options) - 1)]
        last_day = calendar.monthrange(year, month)[1]
        builder.add(
            booked_on=date(year, month, rng.randint(1, last_day)),
            amount=_money_between(rng, low, high),
            direction=OUTGOING,
            raw_description=merchants.pick(rng, pool),
            category=category,
        )


def _plant_anomalies(
    drafts: list[DraftTransaction], rng: Random
) -> list[DraftTransaction]:
    """Deliberately break the pattern in a handful of places.

    The generator knows exactly what it changed, which is what makes the
    ground truth trustworthy later on.
    """
    ordered = sorted(drafts, key=lambda item: (item.booked_on, item.order))
    target = max(4, int(Decimal(len(ordered)) * ANOMALY_RATE))
    next_order = max(item.order for item in ordered) + 1

    spendable = [
        index
        for index, item in enumerate(ordered)
        if item.category in {CATEGORY_GROCERIES, CATEGORY_DINING}
    ]
    subscriptions = [
        index
        for index, item in enumerate(ordered)
        if item.category == CATEGORY_SUBSCRIPTION
    ]

    kinds = (
        ANOMALY_AMOUNT_SPIKE,
        ANOMALY_DUPLICATE,
        ANOMALY_UNUSUAL_MERCHANT,
        ANOMALY_OFF_SCHEDULE,
    )
    extras: list[DraftTransaction] = []

    used: set[int] = set()
    for step in range(target):
        kind = kinds[step % len(kinds)]

        if kind == ANOMALY_AMOUNT_SPIKE and spendable:
            index = _take(rng, spendable, used)
            if index is None:
                continue
            item = ordered[index]
            factor = Decimal(rng.randint(500, 900)) / 100
            ordered[index] = replace(
                item,
                amount=_quantize(item.amount * factor),
                anomaly_kind=ANOMALY_AMOUNT_SPIKE,
            )
        elif kind == ANOMALY_DUPLICATE and spendable:
            index = _take(rng, spendable, used)
            if index is None:
                continue
            item = ordered[index]
            extras.append(
                replace(item, order=next_order, anomaly_kind=ANOMALY_DUPLICATE)
            )
            next_order += 1
        elif kind == ANOMALY_UNUSUAL_MERCHANT:
            reference = ordered[rng.randint(0, len(ordered) - 1)]
            extras.append(
                DraftTransaction(
                    order=next_order,
                    booked_on=reference.booked_on,
                    amount=_money_between(rng, Decimal("1200.00"), Decimal("9500.00")),
                    direction=OUTGOING,
                    raw_description=merchants.pick(rng, merchants.FOREIGN_MERCHANTS),
                    category=CATEGORY_OTHER,
                    anomaly_kind=ANOMALY_UNUSUAL_MERCHANT,
                )
            )
            next_order += 1
        elif kind == ANOMALY_OFF_SCHEDULE and subscriptions:
            index = _take(rng, subscriptions, used)
            if index is None:
                continue
            item = ordered[index]
            shift = rng.randint(9, 16)
            # stay inside the same month so the history keeps the length
            # the caller asked for
            ordered[index] = replace(
                item,
                booked_on=_clamp_day(
                    item.booked_on.year,
                    item.booked_on.month,
                    item.booked_on.day + shift,
                ),
                anomaly_kind=ANOMALY_OFF_SCHEDULE,
            )

    return ordered + extras


def _take(rng: Random, pool: list[int], used: set[int]) -> int | None:
    """Pick an unused index from a pool, or give up after a few tries."""
    for _ in range(12):
        index = pool[rng.randint(0, len(pool) - 1)]
        if index not in used:
            used.add(index)
            return index
    return None


def generate(
    profile: Profile,
    seed: int,
    months: int,
    start: date = DEFAULT_START,
) -> Statement:
    """Build a statement and its ground truth for one profile."""
    rng = Random(seed)
    calendar_months = _months(start, months)

    builder = _Builder()
    _add_income(builder, rng, profile, calendar_months)
    _add_rent(builder, profile, calendar_months)
    _add_subscriptions(builder, rng, profile, calendar_months)
    _add_utilities(builder, rng, profile, calendar_months)
    _add_groceries(builder, rng, profile, start, calendar_months)
    _add_dining(builder, rng, profile, calendar_months)
    _add_big_purchases(builder, rng, profile, calendar_months)

    drafts = _plant_anomalies(builder.drafts, rng)
    drafts.sort(key=lambda item: (item.booked_on, item.order))

    transactions: list[dict] = []
    labels: list[dict] = []
    balance = profile.opening_balance

    for index, draft in enumerate(drafts):
        signed = draft.amount if draft.direction == INCOMING else -draft.amount
        balance = _quantize(balance + signed)
        transaction_id = _transaction_id(profile.name, seed, index)
        transactions.append(
            {
                "id": transaction_id,
                "date": draft.booked_on.isoformat(),
                "amount": f"{_quantize(draft.amount)}",
                "raw_description": draft.raw_description,
                "direction": draft.direction,
                "balance": f"{balance}",
            }
        )
        labels.append(
            {
                "transaction_id": transaction_id,
                "category": draft.category,
                "series_id": (
                    _series_id(profile.name, seed, draft.series_key)
                    if draft.series_key
                    else None
                ),
                "is_anomaly": draft.anomaly_kind is not None,
                "anomaly_kind": draft.anomaly_kind,
            }
        )

    return Statement(transactions=transactions, labels=labels)

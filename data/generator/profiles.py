"""Spending profiles.

Every profile describes one kind of account holder. The generator reads
these numbers and turns them into a statement; nothing here depends on
the seed, so a profile is a pure description of behaviour.
"""

from dataclasses import dataclass, field
from decimal import Decimal


def money(value: str) -> Decimal:
    return Decimal(value)


@dataclass(frozen=True)
class IncomeStream:
    """A recurring incoming payment."""

    name: str
    description: str
    day: int
    day_jitter: int
    amount_low: Decimal
    amount_high: Decimal
    # number of payments per month, inclusive range
    per_month: tuple[int, int] = (1, 1)


@dataclass(frozen=True)
class Subscription:
    """A monthly subscription whose price is raised once or twice."""

    name: str
    description: str
    day: int
    amount: Decimal


@dataclass(frozen=True)
class Utility:
    """A monthly bill whose amount follows the seasons."""

    name: str
    description: str
    day: int
    amount_low: Decimal
    amount_high: Decimal
    # how strongly the bill reacts to cold months
    seasonal: bool = True


@dataclass(frozen=True)
class Profile:
    name: str
    opening_balance: Decimal
    incomes: tuple[IncomeStream, ...]
    subscriptions: tuple[Subscription, ...]
    utilities: tuple[Utility, ...]
    rent_day: int | None
    rent_amount: Decimal | None
    grocery_visits_per_week: tuple[int, int]
    grocery_amount: tuple[Decimal, Decimal]
    dining_per_month: tuple[int, int]
    dining_amount: tuple[Decimal, Decimal]
    # large one off purchases per twelve months
    big_purchases_per_year: int
    tags: tuple[str, ...] = field(default=())


STUDENT = Profile(
    name="student",
    opening_balance=money("4200.00"),
    incomes=(
        IncomeStream(
            name="allowance",
            description="HAVALE - AILE DESTEGI",
            day=1,
            day_jitter=1,
            amount_low=money("6000.00"),
            amount_high=money("6000.00"),
        ),
        IncomeStream(
            name="part_time",
            description="MAAS ODEMESI - KAMPUS KITAPEVI",
            day=15,
            day_jitter=2,
            amount_low=money("4800.00"),
            amount_high=money("5400.00"),
        ),
    ),
    subscriptions=(
        Subscription("spotify", "SPOTIFY AB STOCKHOLM", 8, money("59.99")),
        Subscription("youtube", "GOOGLE YOUTUBE DUBLIN", 19, money("79.99")),
    ),
    utilities=(
        Utility(
            "internet",
            "TURKCELL SUPERONLINE ISTANBUL",
            12,
            money("399.00"),
            money("399.00"),
            seasonal=False,
        ),
        Utility(
            "electricity",
            "ENERJISA ELEKTRIK ANKARA",
            22,
            money("210.00"),
            money("340.00"),
        ),
    ),
    rent_day=3,
    rent_amount=money("6500.00"),
    grocery_visits_per_week=(2, 3),
    grocery_amount=(money("180.00"), money("620.00")),
    dining_per_month=(6, 12),
    dining_amount=(money("90.00"), money("420.00")),
    big_purchases_per_year=1,
)

EMPLOYEE = Profile(
    name="employee",
    opening_balance=money("28500.00"),
    incomes=(
        IncomeStream(
            name="salary",
            description="MAAS ODEMESI - NOVATEK YAZILIM AS",
            day=5,
            day_jitter=2,
            amount_low=money("52000.00"),
            amount_high=money("52000.00"),
        ),
    ),
    subscriptions=(
        Subscription("spotify", "SPOTIFY AB STOCKHOLM", 8, money("59.99")),
        Subscription("netflix", "NETFLIX INTERNATIONAL AMSTERDAM", 14, money("149.99")),
        Subscription("gym", "MACFIT SPOR SALONU ANKARA", 20, money("899.00")),
        Subscription("cloud", "APPLE ICLOUD CORK", 26, money("39.99")),
    ),
    utilities=(
        Utility(
            "internet",
            "TURKCELL SUPERONLINE ISTANBUL",
            12,
            money("649.00"),
            money("649.00"),
            seasonal=False,
        ),
        Utility(
            "electricity",
            "ENERJISA ELEKTRIK ANKARA",
            18,
            money("420.00"),
            money("780.00"),
        ),
        Utility("gas", "BASKENTGAZ ANKARA", 21, money("180.00"), money("1450.00")),
        Utility(
            "water",
            "ASKI SU IDARESI ANKARA",
            25,
            money("160.00"),
            money("280.00"),
            seasonal=False,
        ),
    ),
    rent_day=1,
    rent_amount=money("18500.00"),
    grocery_visits_per_week=(2, 3),
    grocery_amount=(money("450.00"), money("2100.00")),
    dining_per_month=(8, 16),
    dining_amount=(money("180.00"), money("1400.00")),
    big_purchases_per_year=3,
)

FREELANCER = Profile(
    name="freelancer",
    opening_balance=money("41000.00"),
    incomes=(
        IncomeStream(
            name="invoice",
            description="HAVALE - MUSTERI ODEMESI",
            day=11,
            day_jitter=9,
            amount_low=money("14000.00"),
            amount_high=money("68000.00"),
            per_month=(1, 3),
        ),
    ),
    subscriptions=(
        Subscription("adobe", "ADOBE SYSTEMS DUBLIN", 6, money("649.00")),
        Subscription("figma", "FIGMA INC SAN FRANCISCO", 16, money("459.00")),
        Subscription("spotify", "SPOTIFY AB STOCKHOLM", 8, money("59.99")),
    ),
    utilities=(
        Utility(
            "internet",
            "TURKCELL SUPERONLINE ISTANBUL",
            12,
            money("649.00"),
            money("649.00"),
            seasonal=False,
        ),
        Utility(
            "electricity",
            "ENERJISA ELEKTRIK ANKARA",
            18,
            money("380.00"),
            money("720.00"),
        ),
        Utility("gas", "BASKENTGAZ ANKARA", 21, money("150.00"), money("1180.00")),
    ),
    rent_day=2,
    rent_amount=money("15000.00"),
    grocery_visits_per_week=(2, 3),
    grocery_amount=(money("300.00"), money("1600.00")),
    dining_per_month=(10, 20),
    dining_amount=(money("150.00"), money("1100.00")),
    big_purchases_per_year=2,
)

PROFILES = {
    STUDENT.name: STUDENT,
    EMPLOYEE.name: EMPLOYEE,
    FREELANCER.name: FREELANCER,
}

"""Fixtures shared by the backend tests."""

from datetime import date
from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from apps.accounts.models import Account
from apps.transactions.models import (
    AnomalyFlag,
    Budget,
    Category,
    Merchant,
    Subscription,
    Transaction,
)


@pytest.fixture
def api() -> APIClient:
    client = APIClient()
    client.defaults["HTTP_HOST"] = "localhost"
    return client


@pytest.fixture
def account(db) -> Account:
    return Account.objects.create(
        name="employee account",
        profile=Account.Profile.EMPLOYEE,
        opening_balance=Decimal("1000.00"),
        source_seed=42,
    )


@pytest.fixture
def categories(db) -> dict[str, Category]:
    return {
        slug: Category.objects.create(slug=slug, name=slug.title(), is_income=income)
        for slug, income in (
            ("salary", True),
            ("groceries", False),
            ("subscription", False),
        )
    }


@pytest.fixture
def merchant(db, categories) -> Merchant:
    return Merchant.objects.create(
        name="MIGROS MMM ANKARA",
        display_name="Migros",
        category=categories["groceries"],
    )


@pytest.fixture
def transactions(db, account, categories, merchant) -> list[Transaction]:
    """Three outgoing and one incoming movement across two months."""
    rows = [
        Transaction.objects.create(
            account=account,
            external_id="11111111-1111-5111-8111-111111111111",
            date=date(2024, 1, 5),
            amount=Decimal("52000.00"),
            direction=Transaction.Direction.IN,
            raw_description="MAAS ODEMESI - NOVATEK YAZILIM AS",
            balance=Decimal("53000.00"),
            category=categories["salary"],
            series_key="22222222-2222-5222-8222-222222222222",
        ),
        Transaction.objects.create(
            account=account,
            external_id="33333333-3333-5333-8333-333333333333",
            date=date(2024, 1, 10),
            amount=Decimal("650.50"),
            direction=Transaction.Direction.OUT,
            raw_description="MIGROS MMM ANKARA 4527",
            balance=Decimal("52349.50"),
            category=categories["groceries"],
            merchant=merchant,
        ),
        Transaction.objects.create(
            account=account,
            external_id="44444444-4444-5444-8444-444444444444",
            date=date(2024, 2, 8),
            amount=Decimal("149.99"),
            direction=Transaction.Direction.OUT,
            raw_description="NETFLIX INTERNATIONAL AMSTERDAM",
            balance=Decimal("52199.51"),
            category=categories["subscription"],
        ),
        Transaction.objects.create(
            account=account,
            external_id="55555555-5555-5555-8555-555555555555",
            date=date(2024, 2, 20),
            amount=Decimal("2400.00"),
            direction=Transaction.Direction.OUT,
            raw_description="MIGROS MMM ANKARA 8811",
            balance=Decimal("49799.51"),
            category=categories["groceries"],
            merchant=merchant,
        ),
    ]
    return rows


@pytest.fixture
def subscription(db, account, merchant) -> Subscription:
    return Subscription.objects.create(
        account=account,
        merchant=merchant,
        amount=Decimal("149.99"),
        first_seen=date(2024, 1, 14),
        last_seen=date(2024, 2, 14),
    )


@pytest.fixture
def anomaly_flag(db, transactions) -> AnomalyFlag:
    return AnomalyFlag.objects.create(
        transaction=transactions[3],
        kind=AnomalyFlag.Kind.AMOUNT_SPIKE,
        source=AnomalyFlag.Source.GROUND_TRUTH,
    )


@pytest.fixture
def budget(db, account, categories) -> Budget:
    return Budget.objects.create(
        account=account,
        category=categories["groceries"],
        monthly_limit=Decimal("5000.00"),
        starts_on=date(2024, 1, 1),
    )

"""Model level tests."""

from datetime import date
from decimal import Decimal

import pytest
from django.db import IntegrityError

from apps.accounts.models import Account
from apps.transactions.models import Category, Subscription, Transaction

pytestmark = pytest.mark.django_db


def test_account_string_shows_profile(account):
    assert str(account) == "employee account (employee)"


def test_account_gets_a_uuid_primary_key(account):
    assert len(str(account.id)) == 36
    assert account.created_at is not None
    assert account.updated_at is not None


def test_transaction_signed_amount_follows_direction(transactions):
    incoming, outgoing = transactions[0], transactions[1]
    assert incoming.signed_amount == Decimal("52000.00")
    assert outgoing.signed_amount == Decimal("-650.50")


def test_transaction_amount_keeps_two_decimals(transactions):
    stored = Transaction.objects.get(pk=transactions[1].pk)
    assert stored.amount == Decimal("650.50")
    assert isinstance(stored.amount, Decimal)


def test_transaction_external_id_is_unique(account, transactions):
    with pytest.raises(IntegrityError):
        Transaction.objects.create(
            account=account,
            external_id=transactions[0].external_id,
            date=date(2024, 3, 1),
            amount=Decimal("10.00"),
            direction=Transaction.Direction.OUT,
            raw_description="DUPLICATE",
            balance=Decimal("0.00"),
        )


def test_transactions_default_to_newest_first(transactions):
    dates = [item.date for item in Transaction.objects.all()]
    assert dates == sorted(dates, reverse=True)


def test_category_slug_is_unique(categories):
    with pytest.raises(IntegrityError):
        Category.objects.create(slug="groceries", name="Duplicate")


def test_subscription_is_unique_per_account_and_merchant(subscription):
    with pytest.raises(IntegrityError):
        Subscription.objects.create(
            account=subscription.account,
            merchant=subscription.merchant,
            cadence=Subscription.Cadence.MONTHLY,
            amount=Decimal("1.00"),
            first_seen=date(2024, 1, 1),
            last_seen=date(2024, 1, 1),
        )


def test_account_is_unique_per_profile_and_seed(account):
    with pytest.raises(IntegrityError):
        Account.objects.create(
            name="clash", profile=account.profile, source_seed=account.source_seed
        )


def test_anomaly_flag_points_at_its_transaction(anomaly_flag, transactions):
    assert anomaly_flag.transaction_id == transactions[3].pk
    assert str(anomaly_flag).startswith("amount_spike on")


def test_deleting_an_account_removes_its_transactions(account, transactions):
    account.delete()
    assert Transaction.objects.count() == 0

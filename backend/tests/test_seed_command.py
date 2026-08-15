"""Tests for the seed_data and clear_data management commands."""

import json

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from apps.accounts.models import Account
from apps.transactions.models import AnomalyFlag, Merchant, Subscription, Transaction

pytestmark = pytest.mark.django_db

SAMPLE = [
    {
        "id": "aaaaaaaa-1111-5111-8111-111111111111",
        "date": "2024-01-05",
        "amount": "52000.00",
        "raw_description": "MAAS ODEMESI - NOVATEK YAZILIM AS",
        "direction": "in",
        "balance": "80500.00",
    },
    {
        "id": "bbbbbbbb-2222-5222-8222-222222222222",
        "date": "2024-01-08",
        "amount": "149.99",
        "raw_description": "NETFLIX INTERNATIONAL AMSTERDAM",
        "direction": "out",
        "balance": "80350.01",
    },
    {
        "id": "cccccccc-3333-5333-8333-333333333333",
        "date": "2024-02-08",
        "amount": "159.99",
        "raw_description": "NETFLIX INTERNATIONAL AMSTERDAM",
        "direction": "out",
        "balance": "80190.02",
    },
    {
        "id": "dddddddd-4444-5444-8444-444444444444",
        "date": "2024-02-12",
        "amount": "4200.00",
        "raw_description": "MIGROS MMM ANKARA 4527",
        "direction": "out",
        "balance": "75990.02",
    },
]

LABELS = [
    {
        "transaction_id": "aaaaaaaa-1111-5111-8111-111111111111",
        "category": "salary",
        "series_id": "eeeeeeee-1111-5111-8111-111111111111",
        "is_anomaly": False,
        "anomaly_kind": None,
    },
    {
        "transaction_id": "bbbbbbbb-2222-5222-8222-222222222222",
        "category": "subscription",
        "series_id": "ffffffff-2222-5222-8222-222222222222",
        "is_anomaly": False,
        "anomaly_kind": None,
    },
    {
        "transaction_id": "cccccccc-3333-5333-8333-333333333333",
        "category": "subscription",
        "series_id": "ffffffff-2222-5222-8222-222222222222",
        "is_anomaly": False,
        "anomaly_kind": None,
    },
    {
        "transaction_id": "dddddddd-4444-5444-8444-444444444444",
        "category": "groceries",
        "series_id": None,
        "is_anomaly": True,
        "anomaly_kind": "amount_spike",
    },
]


@pytest.fixture
def statement(tmp_path):
    source = tmp_path / "transactions_employee_42.json"
    labels = tmp_path / "labels_employee_42.json"
    source.write_text(json.dumps(SAMPLE), encoding="utf-8")
    labels.write_text(json.dumps(LABELS), encoding="utf-8")
    return source


def test_seed_loads_every_row(statement):
    call_command("seed_data", "--file", str(statement))
    assert Transaction.objects.count() == len(SAMPLE)
    assert Account.objects.count() == 1


def test_seed_is_idempotent(statement):
    call_command("seed_data", "--file", str(statement))
    call_command("seed_data", "--file", str(statement))

    assert Transaction.objects.count() == len(SAMPLE)
    assert Account.objects.count() == 1
    assert AnomalyFlag.objects.count() == 1
    assert Subscription.objects.count() == 1


def test_seed_keeps_decimal_precision(statement):
    call_command("seed_data", "--file", str(statement))
    row = Transaction.objects.get(external_id=SAMPLE[1]["id"])
    assert str(row.amount) == "149.99"
    assert str(row.balance) == "80350.01"


def test_seed_applies_ground_truth_categories(statement):
    call_command("seed_data", "--file", str(statement))
    row = Transaction.objects.get(external_id=SAMPLE[0]["id"])
    assert row.category.slug == "salary"


def test_seed_flags_planted_anomalies(statement):
    call_command("seed_data", "--file", str(statement))
    flag = AnomalyFlag.objects.get()
    assert flag.kind == "amount_spike"
    assert flag.source == AnomalyFlag.Source.GROUND_TRUTH


def test_seed_strips_terminal_numbers_from_merchants(statement):
    call_command("seed_data", "--file", str(statement))
    assert Merchant.objects.filter(name="MIGROS MMM ANKARA").exists()


def test_seed_builds_subscriptions_from_recurring_charges(statement):
    call_command("seed_data", "--file", str(statement))
    subscription = Subscription.objects.get()
    assert (
        subscription.amount
        == Transaction.objects.get(external_id=SAMPLE[2]["id"]).amount
    )
    assert str(subscription.first_seen) == "2024-01-08"
    assert str(subscription.last_seen) == "2024-02-08"


def test_seed_rejects_a_missing_file(tmp_path):
    with pytest.raises(CommandError):
        call_command("seed_data", "--file", str(tmp_path / "nope.json"))


def test_seed_rejects_labels_that_do_not_cover_every_row(tmp_path):
    source = tmp_path / "transactions_employee_42.json"
    labels = tmp_path / "labels_employee_42.json"
    source.write_text(json.dumps(SAMPLE), encoding="utf-8")
    labels.write_text(json.dumps(LABELS[:1]), encoding="utf-8")

    with pytest.raises(CommandError):
        call_command("seed_data", "--file", str(source))


def test_clear_data_needs_confirmation(statement):
    call_command("seed_data", "--file", str(statement))
    with pytest.raises(CommandError):
        call_command("clear_data")
    assert Transaction.objects.count() == len(SAMPLE)


def test_clear_data_empties_the_domain_tables(statement):
    call_command("seed_data", "--file", str(statement))
    call_command("clear_data", "--yes")

    assert Transaction.objects.count() == 0
    assert Account.objects.count() == 0
    assert Merchant.objects.count() == 0
    assert AnomalyFlag.objects.count() == 0

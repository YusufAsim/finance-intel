"""Tests for the synthetic statement generator."""

from datetime import date
from decimal import Decimal

import pytest

from generator.cli import main
from generator.engine import generate
from generator.profiles import PROFILES
from generator.writer import labels_path, transactions_path

MONTHS = 24
SEED = 42

# Rough sanity bounds per profile for a two year history.
EXPECTED_COUNTS = {
    "student": (400, 900),
    "employee": (600, 1100),
    "freelancer": (600, 1200),
}


def build(profile_name: str, seed: int = SEED, months: int = MONTHS):
    return generate(PROFILES[profile_name], seed=seed, months=months)


def test_same_seed_produces_identical_output(profile_name: str) -> None:
    first = build(profile_name)
    second = build(profile_name)
    assert first.transactions == second.transactions
    assert first.labels == second.labels


def test_different_seed_produces_different_output(profile_name: str) -> None:
    assert (
        build(profile_name, seed=SEED).transactions
        != build(profile_name, seed=SEED + 1).transactions
    )


def test_transaction_count_is_in_a_sane_range(profile_name: str) -> None:
    low, high = EXPECTED_COUNTS[profile_name]
    assert low <= len(build(profile_name).transactions) <= high


def test_balance_follows_every_movement(profile_name: str) -> None:
    statement = build(profile_name)
    balance = PROFILES[profile_name].opening_balance
    for transaction in statement.transactions:
        amount = Decimal(transaction["amount"])
        balance += amount if transaction["direction"] == "in" else -amount
        assert Decimal(transaction["balance"]) == balance


def test_labels_match_transactions_one_to_one(profile_name: str) -> None:
    statement = build(profile_name)
    transaction_ids = [item["id"] for item in statement.transactions]
    label_ids = [item["transaction_id"] for item in statement.labels]
    assert transaction_ids == label_ids
    assert len(set(transaction_ids)) == len(transaction_ids)


def test_history_covers_the_requested_months(profile_name: str) -> None:
    statement = build(profile_name)
    first = date.fromisoformat(statement.transactions[0]["date"])
    last = date.fromisoformat(statement.transactions[-1]["date"])
    span = (last.year - first.year) * 12 + (last.month - first.month) + 1
    assert span == MONTHS


def test_transactions_are_ordered_by_date(profile_name: str) -> None:
    dates = [item["date"] for item in build(profile_name).transactions]
    assert dates == sorted(dates)


def test_amounts_are_positive_with_two_decimals(profile_name: str) -> None:
    for transaction in build(profile_name).transactions:
        amount = Decimal(transaction["amount"])
        assert amount > 0
        assert -amount.as_tuple().exponent == 2


def test_recurring_series_span_the_whole_history(profile_name: str) -> None:
    counts: dict[str, int] = {}
    for label in build(profile_name).labels:
        if label["series_id"]:
            counts[label["series_id"]] = counts.get(label["series_id"], 0) + 1
    assert counts, "expected at least one recurring series"
    assert max(counts.values()) >= 20


def test_anomaly_share_stays_low(profile_name: str) -> None:
    statement = build(profile_name)
    planted = [label for label in statement.labels if label["is_anomaly"]]
    share = len(planted) / len(statement.transactions)
    assert 0.01 <= share <= 0.03
    for label in planted:
        assert label["anomaly_kind"] is not None
    for label in statement.labels:
        if not label["is_anomaly"]:
            assert label["anomaly_kind"] is None


def test_every_profile_generates_without_error() -> None:
    for name in PROFILES:
        assert build(name).transactions


def test_cli_writes_both_files(tmp_path) -> None:
    exit_code = main(
        [
            "--seed",
            str(SEED),
            "--profile",
            "employee",
            "--months",
            "6",
            "--out",
            str(tmp_path),
        ]
    )
    assert exit_code == 0
    assert transactions_path(tmp_path, "employee", SEED).exists()
    assert labels_path(tmp_path, "employee", SEED).exists()


def test_cli_rejects_an_empty_history(tmp_path) -> None:
    with pytest.raises(SystemExit):
        main(["--seed", "1", "--months", "0", "--out", str(tmp_path)])


def test_written_files_are_byte_identical_across_runs(tmp_path) -> None:
    args = ["--seed", "5", "--profile", "student", "--months", "6", "--out"]
    main([*args, str(tmp_path / "first")])
    main([*args, str(tmp_path / "second")])
    first = transactions_path(tmp_path / "first", "student", 5).read_bytes()
    second = transactions_path(tmp_path / "second", "student", 5).read_bytes()
    assert first == second

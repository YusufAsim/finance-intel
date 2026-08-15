"""Endpoint, filter and ordering tests."""

import pytest

pytestmark = pytest.mark.django_db


def test_healthz_is_open(api):
    response = api.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_transaction_list_is_paginated(api, transactions):
    payload = api.get("/api/transactions/").json()
    assert set(payload) == {"count", "next", "previous", "results"}
    assert payload["count"] == 4


def test_transaction_detail_returns_the_row(api, transactions):
    row = transactions[1]
    payload = api.get(f"/api/transactions/{row.pk}/").json()
    assert payload["raw_description"] == "MIGROS MMM ANKARA 4527"
    assert payload["category_slug"] == "groceries"
    assert payload["merchant_name"] == "MIGROS MMM ANKARA"


def test_unknown_transaction_returns_404(api, db):
    missing = "99999999-9999-5999-8999-999999999999"
    assert api.get(f"/api/transactions/{missing}/").status_code == 404


def test_filter_by_date_range(api, transactions):
    payload = api.get(
        "/api/transactions/?date_after=2024-02-01&date_before=2024-02-28"
    ).json()
    assert payload["count"] == 2
    assert all(row["date"].startswith("2024-02") for row in payload["results"])


def test_filter_by_category_slug(api, transactions):
    payload = api.get("/api/transactions/?category=groceries").json()
    assert payload["count"] == 2
    assert {row["category_slug"] for row in payload["results"]} == {"groceries"}


def test_filter_by_amount_range(api, transactions):
    payload = api.get("/api/transactions/?amount_min=600&amount_max=3000").json()
    amounts = sorted(float(row["amount"]) for row in payload["results"])
    assert amounts == [650.5, 2400.0]


def test_filter_by_account(api, account, transactions):
    payload = api.get(f"/api/transactions/?account={account.pk}").json()
    assert payload["count"] == 4


def test_filter_by_direction(api, transactions):
    payload = api.get("/api/transactions/?direction=in").json()
    assert payload["count"] == 1


def test_search_matches_the_raw_description(api, transactions):
    payload = api.get("/api/transactions/?search=NETFLIX").json()
    assert payload["count"] == 1


def test_ordering_by_amount_descending(api, transactions):
    payload = api.get("/api/transactions/?ordering=-amount").json()
    amounts = [float(row["amount"]) for row in payload["results"]]
    assert amounts == sorted(amounts, reverse=True)


def test_account_list_reports_transaction_count(api, account, transactions):
    payload = api.get("/api/accounts/").json()
    assert payload["results"][0]["transaction_count"] == 4


def test_category_list_is_available(api, categories):
    assert api.get("/api/categories/").json()["count"] == 3


def test_merchant_list_is_available(api, merchant):
    payload = api.get("/api/merchants/").json()
    assert payload["results"][0]["category_slug"] == "groceries"


def test_subscription_list_is_available(api, subscription):
    payload = api.get("/api/subscriptions/").json()
    assert payload["results"][0]["merchant_name"] == "MIGROS MMM ANKARA"


def test_budget_list_is_available(api, budget):
    payload = api.get("/api/budgets/").json()
    assert payload["results"][0]["category_slug"] == "groceries"


def test_anomaly_flag_list_is_read_only(api, anomaly_flag):
    assert api.get("/api/anomaly-flags/").json()["count"] == 1
    assert api.post("/api/anomaly-flags/", {}, format="json").status_code == 405


def test_transaction_list_avoids_extra_queries(
    api, transactions, django_assert_num_queries
):
    with django_assert_num_queries(2):
        api.get("/api/transactions/")

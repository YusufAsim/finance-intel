"""Tests for the account insight endpoints, with the ml service faked."""

from decimal import Decimal

import pytest

from apps.insights import views
from apps.insights.clients import MlServiceError

pytestmark = pytest.mark.django_db


def test_summary_totals_match_the_stored_rows(api, account, transactions):
    payload = api.get(f"/api/accounts/{account.pk}/summary/").json()
    assert payload["total_income"] == "52000.00"
    assert payload["total_expense"] == "3200.49"
    assert payload["net"] == "48799.51"
    assert payload["transaction_count"] == 4


def test_summary_breaks_spending_down_by_category(api, account, transactions):
    payload = api.get(f"/api/accounts/{account.pk}/summary/").json()
    by_slug = {row["category"]: row for row in payload["categories"]}
    assert by_slug["groceries"]["total"] == "3050.50"
    assert by_slug["groceries"]["count"] == 2
    assert sum(row["share"] for row in payload["categories"]) == pytest.approx(
        1.0, abs=0.001
    )


def test_summary_reports_the_covered_period(api, account, transactions):
    payload = api.get(f"/api/accounts/{account.pk}/summary/").json()
    assert payload["period"] == {"start": "2024-01-05", "end": "2024-02-20"}


def test_summary_of_an_unknown_account_is_404(api, db):
    missing = "99999999-9999-5999-8999-999999999999"
    assert api.get(f"/api/accounts/{missing}/summary/").status_code == 404


def test_subscriptions_endpoint_lists_recurring_charges(api, account, subscription):
    payload = api.get(f"/api/accounts/{account.pk}/subscriptions/").json()
    assert payload["count"] == 1
    assert payload["results"][0]["amount"] == "149.99"


def test_anomalies_endpoint_lists_flags(api, account, anomaly_flag):
    payload = api.get(f"/api/accounts/{account.pk}/anomalies/").json()
    assert payload["count"] == 1
    assert payload["results"][0]["kind"] == "amount_spike"


def test_anomalies_can_be_filtered_by_kind(api, account, anomaly_flag):
    payload = api.get(f"/api/accounts/{account.pk}/anomalies/?kind=duplicate").json()
    assert payload["count"] == 0


def test_forecast_passes_the_history_to_the_ml_service(
    api, account, transactions, monkeypatch
):
    captured = {}

    def fake_forecast(self, history, horizon_days):
        captured["history"] = history
        captured["horizon"] = horizon_days
        return {"points": [], "confidence": 0.8}

    monkeypatch.setattr(views.MlClient, "forecast", fake_forecast)
    payload = api.get(f"/api/accounts/{account.pk}/forecast/?horizon_days=45").json()

    assert payload["horizon_days"] == 45
    assert payload["confidence"] == 0.8
    assert len(captured["history"]) == 4
    assert captured["horizon"] == 45


def test_forecast_horizon_is_clamped(api, account, transactions, monkeypatch):
    monkeypatch.setattr(
        views.MlClient,
        "forecast",
        lambda self, history, horizon_days: {"points": [], "confidence": 0.5},
    )
    payload = api.get(f"/api/accounts/{account.pk}/forecast/?horizon_days=9999").json()
    assert payload["horizon_days"] == 365


def test_forecast_reports_an_unavailable_ml_service(
    api, account, transactions, monkeypatch
):
    def explode(self, history, horizon_days):
        raise MlServiceError("ml service is unreachable")

    monkeypatch.setattr(views.MlClient, "forecast", explode)
    response = api.get(f"/api/accounts/{account.pk}/forecast/")

    assert response.status_code == 503
    assert response.json() == {"detail": "ml service is unreachable"}
    assert "Traceback" not in response.content.decode()


def test_summary_handles_an_account_without_transactions(api, account):
    payload = api.get(f"/api/accounts/{account.pk}/summary/").json()
    assert payload["total_income"] == "0.00"
    assert payload["categories"] == []
    assert payload["period"] == {"start": None, "end": None}


def test_backend_never_imports_model_libraries():
    """The ml stack must not leak into this service."""
    import importlib.util

    for module in ("pandas", "sklearn", "lightgbm"):
        assert importlib.util.find_spec(module) is None


def test_signed_amount_is_exposed_as_a_decimal_string(api, transactions):
    payload = api.get("/api/transactions/?direction=out&ordering=amount").json()
    assert payload["results"][0]["signed_amount"] == str(-Decimal("149.99"))

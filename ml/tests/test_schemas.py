"""Schema validation tests."""

import pytest
from pydantic import ValidationError

from app.clients.backend import BackendClient, BackendError
from app.schemas import ForecastRequest, TransactionBatch, TransactionIn

PATHS = ("/categorize", "/recurring", "/anomaly", "/forecast")

VALID = {
    "date": "2024-01-05",
    "amount": "52000.00",
    "direction": "in",
    "raw_description": "MAAS ODEMESI",
}


def test_transaction_accepts_a_complete_row():
    row = TransactionIn(**VALID)
    assert row.direction == "in"
    assert str(row.amount) == "52000.00"


@pytest.mark.parametrize(
    "override",
    [
        {"amount": "0"},
        {"amount": "-1"},
        {"direction": "sideways"},
        {"date": "not-a-date"},
        {"raw_description": ""},
    ],
)
def test_transaction_rejects_bad_values(override):
    with pytest.raises(ValidationError):
        TransactionIn(**{**VALID, **override})


def test_transaction_requires_every_mandatory_field():
    with pytest.raises(ValidationError):
        TransactionIn(date="2024-01-05")


def test_batch_rejects_an_empty_list():
    with pytest.raises(ValidationError):
        TransactionBatch(transactions=[])


def test_forecast_horizon_has_bounds():
    assert ForecastRequest(transactions=[VALID]).horizon_days == 30
    with pytest.raises(ValidationError):
        ForecastRequest(transactions=[VALID], horizon_days=0)
    with pytest.raises(ValidationError):
        ForecastRequest(transactions=[VALID], horizon_days=400)


@pytest.mark.parametrize("path", PATHS)
def test_endpoints_reject_an_empty_batch(client, path):
    assert client.post(path, json={"transactions": []}).status_code == 422


@pytest.mark.parametrize("path", PATHS)
def test_endpoints_reject_a_malformed_row(client, path):
    response = client.post(path, json={"transactions": [{"date": "2024-01-01"}]})
    assert response.status_code == 422


def test_backend_client_reports_an_unreachable_service(monkeypatch):
    """The client fails loudly instead of returning half an answer."""
    import httpx

    def explode(*args, **kwargs):
        raise httpx.ConnectError("no route to host")

    monkeypatch.setattr(httpx, "get", explode)
    with pytest.raises(BackendError):
        BackendClient(base_url="http://backend:8000").accounts()

"""Smoke tests for the prediction endpoints."""

import pytest

PATHS = ("/categorize", "/recurring", "/anomaly", "/forecast")


def test_healthz_is_open(client):
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_openapi_documents_every_route(client):
    paths = client.get("/openapi.json").json()["paths"]
    for path in PATHS:
        assert path in paths


@pytest.mark.parametrize("path", PATHS)
def test_endpoint_answers_with_a_confidence(client, batch, path):
    response = client.post(path, json={"transactions": batch})
    payload = response.json()

    assert response.status_code == 200
    assert 0 <= payload["confidence"] <= 1
    assert payload["model_version"] == "stub-0.1.0"


def test_categorize_labels_every_transaction(client, batch):
    payload = client.post("/categorize", json={"transactions": batch}).json()
    predictions = payload["predictions"]

    assert len(predictions) == len(batch)
    assert [row["transaction_id"] for row in predictions] == [
        row["id"] for row in batch
    ]
    by_id = {row["transaction_id"]: row["category"] for row in predictions}
    assert by_id["t1"] == "salary"
    assert by_id["t2"] == "subscription"
    assert by_id["t5"] == "groceries"


def test_recurring_groups_a_repeating_merchant(client, batch):
    payload = client.post("/recurring", json={"transactions": batch}).json()
    series = payload["series"]

    assert len(series) == 1
    assert series[0]["merchant"] == "NETFLIX INTERNATIONAL AMSTERDAM"
    assert series[0]["occurrences"] == 3
    assert series[0]["cadence"] == "monthly"
    assert series[0]["transaction_ids"] == ["t2", "t3", "t4"]


def test_recurring_returns_nothing_for_a_single_charge(client):
    payload = client.post(
        "/recurring",
        json={
            "transactions": [
                {
                    "id": "solo",
                    "date": "2024-01-01",
                    "amount": "10.00",
                    "direction": "out",
                    "raw_description": "ONE OFF SHOP 1234",
                }
            ]
        },
    ).json()
    assert payload["series"] == []
    assert payload["confidence"] == 0


def test_anomaly_flags_the_outlier(client, batch):
    payload = client.post("/anomaly", json={"transactions": batch}).json()
    flagged = [row for row in payload["scores"] if row["is_anomaly"]]

    assert len(payload["scores"]) == len(batch)
    assert [row["transaction_id"] for row in flagged] == ["t6"]
    assert flagged[0]["kind"] == "amount_spike"


def test_forecast_returns_one_point_per_day(client, batch):
    payload = client.post(
        "/forecast", json={"transactions": batch, "horizon_days": 14}
    ).json()

    assert payload["horizon_days"] == 14
    assert len(payload["points"]) == 14
    # projection starts the day after the last known movement
    assert payload["points"][0]["date"] == "2024-03-28"


def test_forecast_defaults_to_thirty_days(client, batch):
    payload = client.post("/forecast", json={"transactions": batch}).json()
    assert payload["horizon_days"] == 30
    assert len(payload["points"]) == 30

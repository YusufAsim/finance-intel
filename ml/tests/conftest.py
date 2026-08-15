"""Fixtures for the ml service tests."""

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.main import app  # noqa: E402


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def batch() -> list[dict]:
    """A small statement with one recurring series and one large charge."""
    return [
        {
            "id": "t1",
            "date": "2024-01-05",
            "amount": "52000.00",
            "direction": "in",
            "raw_description": "MAAS ODEMESI - NOVATEK YAZILIM AS",
        },
        {
            "id": "t2",
            "date": "2024-01-08",
            "amount": "149.99",
            "direction": "out",
            "raw_description": "NETFLIX INTERNATIONAL AMSTERDAM",
        },
        {
            "id": "t3",
            "date": "2024-02-08",
            "amount": "159.99",
            "direction": "out",
            "raw_description": "NETFLIX INTERNATIONAL AMSTERDAM",
        },
        {
            "id": "t4",
            "date": "2024-03-08",
            "amount": "169.99",
            "direction": "out",
            "raw_description": "NETFLIX INTERNATIONAL AMSTERDAM",
        },
        {
            "id": "t5",
            "date": "2024-03-12",
            "amount": "620.00",
            "direction": "out",
            "raw_description": "MIGROS MMM ANKARA 4527",
        },
        {
            "id": "t6",
            "date": "2024-03-19",
            "amount": "4200.00",
            "direction": "out",
            "raw_description": "MIGROS MMM ANKARA 8811",
        },
        {
            "id": "t7",
            "date": "2024-03-22",
            "amount": "580.00",
            "direction": "out",
            "raw_description": "MIGROS MMM ANKARA 1290",
        },
        {
            "id": "t8",
            "date": "2024-03-27",
            "amount": "640.00",
            "direction": "out",
            "raw_description": "MIGROS MMM ANKARA 3311",
        },
    ]

"""Tests for request timing and structured logging."""

import json
import logging
import sys

import pytest

from config.logging import JsonFormatter, build_config

pytestmark = pytest.mark.django_db


def test_response_carries_a_timing_header(api):
    response = api.get("/healthz")
    assert response["X-Response-Time"].endswith("ms")
    assert float(response["X-Response-Time"].removesuffix("ms")) >= 0


def test_request_log_is_json_with_the_expected_fields(api, caplog):
    with caplog.at_level(logging.INFO, logger="request"):
        api.get("/healthz")

    record = next(item for item in caplog.records if item.name == "request")
    payload = json.loads(JsonFormatter().format(record))

    assert payload["path"] == "/healthz"
    assert payload["method"] == "GET"
    assert payload["status_code"] == 200
    assert payload["duration_ms"] >= 0
    assert payload["level"] == "INFO"
    assert payload["logger"] == "request"


def test_formatter_renders_exceptions():
    logger = logging.getLogger("probe")
    try:
        raise ValueError("boom")
    except ValueError:
        record = logger.makeRecord(
            "probe", logging.ERROR, __file__, 1, "failed", None, sys.exc_info()
        )
    payload = json.loads(JsonFormatter().format(record))
    assert "ValueError" in payload["exception"]


def test_log_level_comes_from_the_environment():
    assert build_config("DEBUG")["root"]["level"] == "DEBUG"
    assert build_config("WARNING")["root"]["level"] == "WARNING"


def test_noisy_loggers_are_quietened():
    config = build_config("INFO")
    assert config["loggers"]["django.server"]["level"] == "WARNING"
    assert config["loggers"]["django.db.backends"]["level"] == "WARNING"

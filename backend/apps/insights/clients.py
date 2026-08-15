"""Thin http client for the ml service.

The backend never imports model libraries. Everything it needs from a
model arrives over this contract, and a failure here is reported as an
unavailable dependency rather than leaking upstream details.
"""

import logging

import httpx
from django.conf import settings

logger = logging.getLogger(__name__)


class MlServiceError(RuntimeError):
    """Raised when the ml service cannot answer."""


class MlClient:
    def __init__(self, base_url: str | None = None, timeout: float | None = None):
        self.base_url = (base_url or settings.ML_BASE_URL).rstrip("/")
        self.timeout = timeout or settings.ML_TIMEOUT_SECONDS

    def _post(self, path: str, payload: dict) -> dict:
        url = f"{self.base_url}{path}"
        try:
            response = httpx.post(url, json=payload, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as exc:
            logger.warning(
                "ml service returned %s for %s", exc.response.status_code, path
            )
            raise MlServiceError(
                f"ml service returned {exc.response.status_code}"
            ) from exc
        except httpx.HTTPError as exc:
            logger.warning("ml service unreachable at %s", url)
            raise MlServiceError("ml service is unreachable") from exc

    def forecast(self, transactions: list[dict], horizon_days: int) -> dict:
        """Ask for a cash flow projection over the next horizon."""
        return self._post(
            "/forecast",
            {"transactions": transactions, "horizon_days": horizon_days},
        )

    def categorize(self, transactions: list[dict]) -> dict:
        """Ask for category predictions on a batch of transactions."""
        return self._post("/categorize", {"transactions": transactions})

    def recurring(self, transactions: list[dict]) -> dict:
        """Ask which transactions form recurring series."""
        return self._post("/recurring", {"transactions": transactions})

    def anomaly(self, transactions: list[dict]) -> dict:
        """Ask for anomaly scores on a batch of transactions."""
        return self._post("/anomaly", {"transactions": transactions})

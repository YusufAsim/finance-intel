"""Async http client for the backend service.

Every method maps to exactly one backend endpoint. No aggregation, no
business logic: the tool layer above only forwards what arrives here.
"""

import logging

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)


class UpstreamError(RuntimeError):
    """Raised when an upstream service cannot answer."""


class BackendClient:
    def __init__(self, base_url: str | None = None, timeout: float | None = None):
        settings = get_settings()
        self.base_url = (base_url or settings.backend_base_url).rstrip("/")
        self.timeout = timeout or settings.http_timeout_seconds

    async def _get(self, path: str, params: dict | None = None) -> dict:
        url = f"{self.base_url}{path}"
        cleaned = {k: v for k, v in (params or {}).items() if v is not None}
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=cleaned)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            logger.warning("backend returned %s for %s", status, path)
            raise UpstreamError(f"backend returned {status} for {path}") from exc
        except httpx.HTTPError as exc:
            logger.warning("backend unreachable at %s", url)
            raise UpstreamError("backend is unreachable") from exc

    async def list_transactions(self, **params) -> dict:
        return await self._get("/api/transactions/", params)

    async def list_merchants(self, **params) -> dict:
        return await self._get("/api/merchants/", params)

    async def list_accounts(self, **params) -> dict:
        return await self._get("/api/accounts/", params)

    async def account_summary(self, account_id: str) -> dict:
        return await self._get(f"/api/accounts/{account_id}/summary/")

    async def account_subscriptions(self, account_id: str) -> dict:
        return await self._get(f"/api/accounts/{account_id}/subscriptions/")

    async def account_anomalies(self, account_id: str, kind: str | None = None) -> dict:
        return await self._get(f"/api/accounts/{account_id}/anomalies/", {"kind": kind})

    async def account_forecast(self, account_id: str, horizon_days: int) -> dict:
        return await self._get(
            f"/api/accounts/{account_id}/forecast/", {"horizon_days": horizon_days}
        )

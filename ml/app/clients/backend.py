"""Http client for the backend service.

Training data is pulled over the rest api. The ml service has no
database driver and never talks to postgres directly.
"""

import logging

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)


class BackendError(RuntimeError):
    """Raised when the backend cannot answer."""


class BackendClient:
    def __init__(self, base_url: str | None = None, timeout: float | None = None):
        settings = get_settings()
        self.base_url = (base_url or settings.backend_base_url).rstrip("/")
        self.timeout = timeout or settings.backend_timeout_seconds

    def _get(self, path: str, params: dict | None = None) -> dict:
        url = f"{self.base_url}{path}"
        try:
            response = httpx.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as exc:
            raise BackendError(
                f"backend returned {exc.response.status_code} for {path}"
            ) from exc
        except httpx.HTTPError as exc:
            logger.warning("backend unreachable at %s", url)
            raise BackendError("backend is unreachable") from exc

    def transactions(self, account_id: str, page_size: int = 500) -> list[dict]:
        """Pull every transaction of an account, following pagination."""
        collected: list[dict] = []
        payload = self._get(
            "/api/transactions/",
            {"account": account_id, "page_size": page_size},
        )
        collected.extend(payload.get("results", []))
        while payload.get("next"):
            payload = self._get_absolute(payload["next"])
            collected.extend(payload.get("results", []))
        return collected

    def _get_absolute(self, url: str) -> dict:
        try:
            response = httpx.get(url, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as exc:
            raise BackendError("backend is unreachable") from exc

    def accounts(self) -> list[dict]:
        return self._get("/api/accounts/").get("results", [])

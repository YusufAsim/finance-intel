"""HTTP entry point for the mcp service.

The tool surface is mounted next to a plain health route, so the service
answers orchestration probes as well as tool traffic.
"""

import logging

from fastapi import FastAPI

from app.config import get_settings
from app.tools.finance import mcp

settings = get_settings()
logging.basicConfig(level=settings.log_level)

app = FastAPI(title="finance-intel mcp", version="0.1.0")


@app.get("/healthz")
def healthz() -> dict[str, str]:
    """Report liveness of the tool surface."""
    return {"status": "ok"}


# the mcp protocol endpoints live under /mcp
app.mount("/mcp", mcp.http_app(path="/"))

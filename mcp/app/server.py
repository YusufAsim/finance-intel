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

# the mcp protocol endpoints live under /mcp, and the session manager it
# starts has to run inside the parent application's lifespan
mcp_app = mcp.http_app(path="/")

app = FastAPI(title="finance-intel mcp", version="0.1.0", lifespan=mcp_app.lifespan)


@app.get("/healthz")
def healthz() -> dict[str, str]:
    """Report liveness of the tool surface."""
    return {"status": "ok"}


app.mount("/mcp", mcp_app)

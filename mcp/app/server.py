"""HTTP entry point for the mcp service.

The tool surface itself is mounted on top of this application, so the
service can answer plain health probes as well as tool traffic.
"""

from fastapi import FastAPI

app = FastAPI(title="finance-intel mcp", version="0.1.0")


@app.get("/healthz")
def healthz() -> dict[str, str]:
    """Report liveness of the tool surface."""
    return {"status": "ok"}

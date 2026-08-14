"""FastAPI application for the agentic service."""

from fastapi import FastAPI

app = FastAPI(title="finance-intel agentic", version="0.1.0")


@app.get("/healthz")
def healthz() -> dict[str, str]:
    """Report liveness without touching any model provider."""
    return {"status": "ok"}

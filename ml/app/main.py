"""FastAPI application for the ml service."""

from fastapi import FastAPI

app = FastAPI(title="finance-intel ml", version="0.1.0")


@app.get("/healthz")
def healthz() -> dict[str, str]:
    """Report liveness. Stays green even when no model is loaded."""
    return {"status": "ok"}

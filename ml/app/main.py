"""FastAPI application for the ml service."""

import logging

from fastapi import FastAPI

from app.config import get_settings
from app.routers import predictions

settings = get_settings()
logging.basicConfig(level=settings.log_level)

app = FastAPI(title="finance-intel ml", version="0.1.0")
app.include_router(predictions.router)


@app.get("/healthz")
def healthz() -> dict[str, str]:
    """Report liveness. Stays green even when no model is loaded."""
    return {"status": "ok"}

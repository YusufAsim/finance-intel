"""Prediction endpoints.

Every route is a stub for now. The request and response schemas are the
real ones, so swapping in a trained model later does not change the
contract other services rely on.
"""

from fastapi import APIRouter

from app.pipelines import stubs
from app.schemas import (
    AnomalyResponse,
    CategorizeResponse,
    ForecastRequest,
    ForecastResponse,
    RecurringResponse,
    TransactionBatch,
)

router = APIRouter(tags=["predictions"])


@router.post("/categorize", response_model=CategorizeResponse)
def categorize(batch: TransactionBatch) -> CategorizeResponse:
    """Predict a spending category for every transaction in the batch."""
    predictions, confidence = stubs.categorize(batch.transactions)
    return CategorizeResponse(
        model_version=stubs.MODEL_VERSION,
        predictions=predictions,
        confidence=confidence,
    )


@router.post("/recurring", response_model=RecurringResponse)
def recurring(batch: TransactionBatch) -> RecurringResponse:
    """Report which transactions look like a repeating series."""
    series, confidence = stubs.recurring(batch.transactions)
    return RecurringResponse(
        model_version=stubs.MODEL_VERSION, series=series, confidence=confidence
    )


@router.post("/anomaly", response_model=AnomalyResponse)
def anomaly(batch: TransactionBatch) -> AnomalyResponse:
    """Score every transaction on how far it sits from the usual pattern."""
    scores, confidence = stubs.anomaly(batch.transactions)
    return AnomalyResponse(
        model_version=stubs.MODEL_VERSION, scores=scores, confidence=confidence
    )


@router.post("/forecast", response_model=ForecastResponse)
def forecast(request: ForecastRequest) -> ForecastResponse:
    """Project cash flow forward over the requested horizon."""
    points, confidence = stubs.forecast(request.transactions, request.horizon_days)
    return ForecastResponse(
        model_version=stubs.MODEL_VERSION,
        horizon_days=request.horizon_days,
        points=points,
        confidence=confidence,
    )

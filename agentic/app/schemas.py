"""Request and response models for the agentic service."""

from typing import Any

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=1000)
    account_id: str | None = None


class ChatResponse(BaseModel):
    question: str
    intent: str
    tool_name: str | None
    answer: str
    tool_results: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None

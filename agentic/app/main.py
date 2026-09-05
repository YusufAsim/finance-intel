"""FastAPI application for the agentic service."""

import logging

from fastapi import FastAPI

from app.config import get_settings
from app.graph.build import get_graph
from app.schemas import ChatRequest, ChatResponse

settings = get_settings()
logging.basicConfig(level=settings.log_level)

app = FastAPI(title="finance-intel agentic", version="0.1.0")


@app.get("/healthz")
def healthz() -> dict[str, str]:
    """Report liveness without touching any model provider."""
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """Answer a question by routing it and calling one mcp tool."""
    state = await get_graph().ainvoke(
        {"question": request.question, "account_id": request.account_id}
    )
    return ChatResponse(
        question=state["question"],
        intent=state["intent"],
        tool_name=state.get("tool_name"),
        answer=state["answer"],
        tool_results=state.get("tool_results") or {},
        error=state.get("error"),
    )

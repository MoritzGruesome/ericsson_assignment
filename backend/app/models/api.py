from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field

from app.agents.models import Citation


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4_000)
    conversation_id: str | None = Field(default=None, max_length=255)
    employee_id: str | None = Field(default=None, max_length=40)
    as_of_date: date | None = None


class ChatResponse(BaseModel):
    conversation_id: str
    answer: str
    citations: list[Citation]
    assumptions: list[str]
    escalation_required: bool
    escalation_reason: str | None
    agents_used: list[str]
    route: str | None


class HealthResponse(BaseModel):
    status: str
    llm_configured: bool
    policy_index_path: str


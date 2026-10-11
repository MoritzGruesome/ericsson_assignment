from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field

from app.agents.models import Citation


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4_000)
    conversation_id: str | None = Field(default=None, max_length=255)
    employee_id: str | None = Field(default=None, max_length=40)
    as_of_date: date | None = None


class ExecutionStep(BaseModel):
    kind: Literal["agent", "tool"]
    name: str
    label: str
    agent: str | None = None


class ChatResponse(BaseModel):
    conversation_id: str
    answer: str
    citations: list[Citation]
    assumptions: list[str]
    escalation_required: bool
    escalation_reason: str | None
    agents_used: list[str]
    route: str | None
    execution_history: list[ExecutionStep] = Field(default_factory=list)


class HealthResponse(BaseModel):
    status: str
    llm_configured: bool
    policy_index_path: str


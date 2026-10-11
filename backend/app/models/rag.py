from __future__ import annotations

from datetime import date, datetime, time, timezone
from typing import Any

from pydantic import BaseModel, Field


class PolicyChunk(BaseModel):
    chunk_id: str
    text: str
    policy_id: str
    policy_title: str
    version: str
    document_status: str
    effective_date: date
    locations: list[str]
    applies_to: list[str]
    section_number: str
    section_title: str
    source_path: str
    chunk_index: int
    content_hash: str

    def payload(self) -> dict[str, Any]:
        data = self.model_dump(mode="json")
        data["effective_date_epoch"] = int(
            datetime.combine(self.effective_date, time.min, tzinfo=timezone.utc).timestamp()
        )
        return data


class PolicySearchInput(BaseModel):
    query: str = Field(min_length=2, max_length=500)
    as_of_date: date
    location: str | None = None
    employee_type: str | None = None
    policy_ids: list[str] | None = None
    top_k: int = Field(default=6, ge=1, le=10)


class PolicyEvidence(BaseModel):
    chunk_id: str
    policy_id: str
    policy_title: str
    section_number: str
    section_title: str
    text: str
    source_path: str
    effective_date: date
    score: float

    @property
    def citation(self) -> str:
        return f"{self.policy_id} §{self.section_number}"


class PolicySearchResult(BaseModel):
    query: str
    applied_filters: dict[str, Any]
    evidence: list[PolicyEvidence]


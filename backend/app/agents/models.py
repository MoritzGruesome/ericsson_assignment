from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator


MAX_CITATION_EXCERPT_LENGTH = 500


class Citation(BaseModel):
    policy_id: str
    section_number: str
    section_title: str
    source_path: str
    excerpt: str = Field(
        description="A short supporting excerpt copied from the retrieved policy evidence."
    )

    @field_validator("excerpt", mode="before")
    @classmethod
    def normalise_excerpt(cls, value: object) -> str:
        """Keep display citations compact without rejecting an otherwise valid agent report."""
        text = " ".join(str(value).split())
        if len(text) <= MAX_CITATION_EXCERPT_LENGTH:
            return text

        shortened = text[: MAX_CITATION_EXCERPT_LENGTH - 1]
        if " " in shortened:
            shortened = shortened.rsplit(" ", 1)[0]
        return f"{shortened}…"

    @property
    def label(self) -> str:
        return f"{self.policy_id} §{self.section_number}"


class SupervisorDecision(BaseModel):
    route: Literal["direct", "rag", "case", "rag_then_case", "escalate"]
    rationale: str
    rag_task: str | None = None
    case_task: str | None = None
    escalation_reason: str | None = None


class RagAgentReport(BaseModel):
    findings: list[str]
    citations: list[Citation]
    missing_information: list[str]
    conflicts: list[str]
    confidence: Literal["high", "medium", "low"]
    requires_case_analysis: bool = False
    requires_human_escalation: bool = False


class CaseAgentReport(BaseModel):
    conclusions: list[str]
    facts_used: list[str]
    calculations: list[str]
    missing_information: list[str]
    tool_names_used: list[str]
    requires_policy_review: bool = False
    requires_human_escalation: bool = False


class FinalResponse(BaseModel):
    answer_markdown: str
    citations: list[Citation] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    escalation_required: bool = False
    escalation_reason: str | None = None


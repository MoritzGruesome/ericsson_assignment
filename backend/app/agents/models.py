from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator


MAX_CITATION_EXCERPT_LENGTH = 500

EscalationCategory = Literal[
    "missing_information",
    "record_dispute",
    "policy_conflict",
    "legal_or_regulatory",
    "medical_or_accommodation",
    "sensitive_report",
    "suspected_fraud",
    "employment_decision",
    "immediate_safety",
]
EscalationSeverity = Literal["informational", "standard", "urgent", "emergency"]


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


class EscalationAdvice(BaseModel):
    """Typed advice for the Supervisor; specialist advice never controls graph routing."""

    category: EscalationCategory
    severity: EscalationSeverity
    reason: str


class SupervisorDecision(BaseModel):
    route: Literal["direct", "rag", "case", "rag_then_case", "escalate"]
    rationale: str
    rag_task: str | None = None
    case_task: str | None = None
    escalation: EscalationAdvice | None = None


class RagAgentReport(BaseModel):
    findings: list[str]
    citations: list[Citation]
    missing_information: list[str]
    conflicts: list[str]
    confidence: Literal["high", "medium", "low"]
    requires_case_analysis: bool = False
    escalation_advice: EscalationAdvice | None = None


class CaseAgentReport(BaseModel):
    status: Literal["success", "needs_input", "invalid_input"] = "success"
    calculation_basis: Literal["employee_record", "hypothetical_scenario"] | None = None
    conclusions: list[str]
    facts_used: list[str]
    calculations: list[str]
    assumptions: list[str] = Field(default_factory=list)
    missing_information: list[str]
    tool_names_used: list[str]
    requires_policy_review: bool = False
    escalation_advice: EscalationAdvice | None = None


class AnswerSegment(BaseModel):
    text: str
    source_refs: list[str] = Field(min_length=1)


class AnswerBlock(BaseModel):
    kind: Literal["paragraph", "bullet"] = "paragraph"
    segments: list[AnswerSegment] = Field(min_length=1)


class FinalResponse(BaseModel):
    answer_markdown: str
    answer_blocks: list[AnswerBlock] = Field(default_factory=list)
    citations: list[Citation] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    escalation_required: bool = False
    escalation_reason: str | None = None


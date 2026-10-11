from app.agents.models import (
    MAX_CITATION_EXCERPT_LENGTH,
    CaseAgentReport,
    Citation,
    RagAgentReport,
)


def test_long_citation_excerpt_is_truncated_instead_of_rejected() -> None:
    report = RagAgentReport.model_validate(
        {
            "findings": ["Employees in probation may request one remote day per week."],
            "citations": [
                {
                    "policy_id": "HR-WORK-001",
                    "section_number": "2",
                    "section_title": "Eligibility and work arrangement",
                    "source_path": "data/policies/flexible-remote-work.md",
                    "excerpt": "A long retrieved passage " * 40,
                }
            ],
            "missing_information": [],
            "conflicts": [],
            "confidence": "high",
        }
    )

    excerpt = report.citations[0].excerpt
    assert len(excerpt) <= MAX_CITATION_EXCERPT_LENGTH
    assert excerpt.endswith("…")


def test_citation_excerpt_whitespace_is_normalised() -> None:
    citation = Citation(
        policy_id="HR-WORK-001",
        section_number="2",
        section_title="Eligibility",
        source_path="data/policies/flexible-remote-work.md",
        excerpt="One sentence.\n\n   Another sentence.",
    )

    assert citation.excerpt == "One sentence. Another sentence."


def test_case_report_carries_recoverable_tool_status_upward() -> None:
    report = CaseAgentReport(
        status="needs_input",
        conclusions=[],
        facts_used=["As-of date: 2026-10-11"],
        calculations=[],
        missing_information=["start_date"],
        tool_names_used=["calculate_leave_balance"],
    )

    assert report.status == "needs_input"
    assert report.missing_information == ["start_date"]
    assert report.escalation_advice is None


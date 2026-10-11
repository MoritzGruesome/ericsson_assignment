from app.agents.models import MAX_CITATION_EXCERPT_LENGTH, Citation, RagAgentReport


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


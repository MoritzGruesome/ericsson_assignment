from app.agents.graph import (
    detect_safety_escalation,
    escalation_answer,
    route_after_rag_report,
)
from app.agents.models import EscalationAdvice


def _state(route: str, *, requires_case_analysis: bool = False) -> dict:
    return {
        "decision": {
            "route": route,
            "rationale": "Test route",
            "rag_task": "Find the leave policy",
            "case_task": "Calculate the employee balance",
        },
        "rag_report": {
            "findings": ["Annual leave is prorated."],
            "citations": [],
            "missing_information": ["Employee record"] if requires_case_analysis else [],
            "conflicts": [],
            "confidence": "medium",
            "requires_case_analysis": requires_case_analysis,
            "escalation_advice": {
                "category": "missing_information",
                "severity": "informational",
                "reason": "Employee data is needed for the calculation.",
            },
        },
    }


def test_specialist_advice_cannot_preempt_planned_case_analysis() -> None:
    assert route_after_rag_report(_state("rag_then_case")) == "case"


def test_specialist_advice_does_not_enter_escalation_branch() -> None:
    assert route_after_rag_report(_state("rag")) == "final"


def test_rag_can_request_case_analysis_without_escalating() -> None:
    assert route_after_rag_report(_state("rag", requires_case_analysis=True)) == "case"


def test_routine_leave_question_does_not_trigger_safety_gate() -> None:
    question = "I joined on 15 June and took four days off. How much leave is available?"
    assert detect_safety_escalation(question) is None


def test_safety_gate_returns_typed_severity() -> None:
    advice = detect_safety_escalation("Someone has a weapon and I am in immediate danger")
    assert advice is not None
    assert advice.category == "immediate_safety"
    assert advice.severity == "emergency"


def test_sensitive_report_copy_does_not_imply_immediate_danger() -> None:
    answer = escalation_answer(
        EscalationAdvice(
            category="sensitive_report",
            severity="urgent",
            reason="A workplace concern needs confidential review.",
        )
    )

    assert "reviewed confidentially" in answer
    assert "emergency services" not in answer

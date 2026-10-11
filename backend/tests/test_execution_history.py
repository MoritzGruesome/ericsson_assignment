from langchain_core.messages import AIMessage, ToolMessage

from app.agents.graph import _actual_tool_names
from app.api.routes import _execution_history_from_state, _execution_steps_for_update


def test_tool_names_come_from_actual_tool_messages() -> None:
    names = _actual_tool_names(
        {
            "messages": [
                AIMessage(content="I will calculate the balance."),
                ToolMessage(
                    content='{"status":"success"}',
                    tool_call_id="call-1",
                    name="calculate_leave_balance",
                ),
                ToolMessage(
                    content="ignored",
                    tool_call_id="call-2",
                    name="unknown_tool",
                ),
            ]
        },
        {"calculate_leave_balance"},
    )

    assert names == ["calculate_leave_balance"]


def test_case_progress_uses_exact_tool_names() -> None:
    steps = _execution_steps_for_update(
        "employee_case_analyst",
        {
            "case_report": {
                "status": "success",
                "calculation_basis": "employee_record",
                "conclusions": ["Balance calculated."],
                "facts_used": ["NS-1042"],
                "calculations": ["Available balance: 2.29 days"],
                "missing_information": [],
                "tool_names_used": [
                    "get_employee_profile",
                    "calculate_leave_balance",
                    "calculate_leave_balance",
                ],
            }
        },
    )

    assert [step.name for step in steps] == [
        "get_employee_profile",
        "calculate_leave_balance",
    ]
    assert [step.kind for step in steps] == ["tool", "tool"]
    assert steps[1].label == "Case Analyst used calculate_leave_balance"


def test_completed_history_can_be_reconstructed_from_graph_state() -> None:
    history = _execution_history_from_state(
        {
            "decision": {
                "route": "rag_then_case",
                "rationale": "Policy and calculation are both required.",
            },
            "agents_used": ["supervisor", "policy_rag_agent", "employee_case_analyst"],
            "case_report": {
                "conclusions": ["Balance calculated."],
                "facts_used": [],
                "calculations": [],
                "missing_information": [],
                "tool_names_used": ["calculate_leave_balance"],
            },
        }
    )

    assert [step.name for step in history] == [
        "safety_gate",
        "supervisor_plan",
        "search_policies",
        "calculate_leave_balance",
        "supervisor_final",
    ]


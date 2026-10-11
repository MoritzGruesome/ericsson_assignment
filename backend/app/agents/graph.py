from __future__ import annotations

import json
from datetime import date
from typing import Annotated, Any, Literal, TypedDict

from langchain.agents import create_agent
from langchain_core.messages import AIMessage, AnyMessage, HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph, add_messages

from app.agents.models import (
    CaseAgentReport,
    Citation,
    EscalationAdvice,
    FinalResponse,
    RagAgentReport,
    SupervisorDecision,
)
from app.agents.prompts import (
    CASE_AGENT_PROMPT,
    RAG_AGENT_PROMPT,
    SUPERVISOR_PLANNING_PROMPT,
    SUPERVISOR_SYNTHESIS_PROMPT,
)
from app.config import Settings
from app.services.case_service import CaseDataService
from app.services.policy_service import PolicySearchService
from app.tools.factories import create_case_tools, create_policy_search_tool


class AssistantState(TypedDict, total=False):
    messages: Annotated[list[AnyMessage], add_messages]
    employee_id: str | None
    as_of_date: str
    decision: dict[str, Any] | None
    rag_report: dict[str, Any] | None
    case_report: dict[str, Any] | None
    final_response: dict[str, Any] | None
    safety_escalation: dict[str, Any] | None
    agents_used: list[str]


SENSITIVE_RULES: tuple[tuple[EscalationAdvice, tuple[str, ...]], ...] = (
    (
        EscalationAdvice(
            category="immediate_safety",
            severity="emergency",
            reason="The request indicates a possible immediate safety concern.",
        ),
        (
            "immediate danger",
            "violence",
            "weapon",
            "unsafe right now",
            "self-harm",
            "suicide",
        ),
    ),
    (
        EscalationAdvice(
            category="sensitive_report",
            severity="urgent",
            reason="The request appears to report a sensitive workplace conduct concern.",
        ),
        (
            "harassment",
            "discrimination",
            "retaliation",
            "inappropriate comments",
            "bullying",
        ),
    ),
    (
        EscalationAdvice(
            category="suspected_fraud",
            severity="urgent",
            reason="The request appears to report suspected fraud or falsified records.",
        ),
        ("fraud", "falsified records", "stealing from the company"),
    ),
    (
        EscalationAdvice(
            category="employment_decision",
            severity="standard",
            reason="The request asks the assistant to make an employment decision.",
        ),
        (
            "should i fire",
            "should we fire",
            "should i hire",
            "should we hire",
            "disciplinary sanction",
            "promotion decision",
        ),
    ),
)


def detect_safety_escalation(text: str) -> EscalationAdvice | None:
    normalized = text.lower()
    for advice, terms in SENSITIVE_RULES:
        if any(term in normalized for term in terms):
            return advice
    return None


def escalation_answer(advice: EscalationAdvice) -> str:
    if advice.category == "immediate_safety" or advice.severity == "emergency":
        return (
            "This may involve an immediate safety risk. Contact local emergency services first "
            "if anyone may be in danger, then notify Northstar Security and the Hong Kong People "
            "Partner. Please avoid sharing unnecessary sensitive details in this chat."
        )
    if advice.category in {"sensitive_report", "suspected_fraud"}:
        return (
            "This concern should be reviewed confidentially by a person. Contact the fictional "
            "Northstar Hong Kong People Partner at `hk-people-partner@northstar.example` or use "
            "`ethics.northstar.example/report`. Please avoid sharing unnecessary sensitive "
            "details in this chat."
        )
    return (
        "I can explain the relevant policy, but I cannot make this decision. Please contact "
        "the fictional Northstar Hong Kong People Partner at "
        "`hk-people-partner@northstar.example` for a qualified review."
    )


def route_after_rag_report(state: AssistantState) -> Literal["case", "final"]:
    """Specialist advice is evidence for the Supervisor, never a graph terminator."""
    report = RagAgentReport.model_validate(state["rag_report"])
    decision = SupervisorDecision.model_validate(state["decision"])
    if decision.route == "rag_then_case" or report.requires_case_analysis:
        return "case"
    return "final"


def _latest_user_text(state: AssistantState) -> str:
    for message in reversed(state.get("messages", [])):
        if isinstance(message, HumanMessage):
            return str(message.content)
    return ""


def _safe_json(value: Any) -> str:
    if value is None:
        return "null"
    if hasattr(value, "model_dump"):
        value = value.model_dump(mode="json")
    return json.dumps(value, ensure_ascii=False, indent=2)


def _build_model(settings: Settings) -> ChatOpenAI:
    kwargs: dict[str, Any] = {
        "model": settings.llm_model,
        "api_key": settings.openai_api_key,
        "use_responses_api": True,
        "max_retries": 2,
    }
    if not settings.llm_model.startswith(("gpt-5", "gpt-6", "o")):
        kwargs["temperature"] = settings.llm_temperature
    return ChatOpenAI(**kwargs)


def build_graph(
    *,
    settings: Settings,
    policy_service: PolicySearchService,
    case_service: CaseDataService,
    checkpointer=None,
):
    model = _build_model(settings)
    planner = model.with_structured_output(SupervisorDecision)
    synthesizer = model.with_structured_output(FinalResponse)

    rag_agent = create_agent(
        model=model,
        tools=[create_policy_search_tool(policy_service)],
        system_prompt=RAG_AGENT_PROMPT,
        response_format=RagAgentReport,
        name="policy_rag_agent",
    )
    case_agent = create_agent(
        model=model,
        tools=create_case_tools(case_service),
        system_prompt=CASE_AGENT_PROMPT,
        response_format=CaseAgentReport,
        name="employee_case_analyst",
    )

    async def safety_gate(state: AssistantState) -> dict[str, Any]:
        safety_escalation = detect_safety_escalation(_latest_user_text(state))
        return {
            "safety_escalation": (
                safety_escalation.model_dump(mode="json") if safety_escalation else None
            ),
            "decision": None,
            "rag_report": None,
            "case_report": None,
            "final_response": None,
            "agents_used": ["supervisor"],
        }

    def route_after_safety(state: AssistantState) -> Literal["escalate", "plan"]:
        return "escalate" if state.get("safety_escalation") else "plan"

    async def supervisor_plan(state: AssistantState) -> dict[str, Any]:
        user_text = _latest_user_text(state)
        context = (
            f"Current date: {state.get('as_of_date', date.today().isoformat())}\n"
            f"Selected synthetic employee ID: {state.get('employee_id') or 'none'}\n"
            f"Latest user request: {user_text}"
        )
        decision = await planner.ainvoke(
            [
                {"role": "system", "content": SUPERVISOR_PLANNING_PROMPT},
                {"role": "user", "content": context},
            ]
        )
        return {"decision": decision.model_dump(mode="json")}

    def route_after_plan(
        state: AssistantState,
    ) -> Literal["rag", "case", "final", "escalate"]:
        decision = SupervisorDecision.model_validate(state["decision"])
        return {
            "rag": "rag",
            "rag_then_case": "rag",
            "case": "case",
            "direct": "final",
            "escalate": "escalate",
        }[decision.route]

    async def run_rag_agent(state: AssistantState) -> dict[str, Any]:
        decision = SupervisorDecision.model_validate(state["decision"])
        prompt = (
            f"Supervisor task: {decision.rag_task}\n"
            f"Original request: {_latest_user_text(state)}\n"
            f"As-of date: {state.get('as_of_date')}\n"
            f"Employee location hint: use the selected employee only if supplied; employee ID is "
            f"{state.get('employee_id') or 'not supplied'}."
        )
        result = await rag_agent.ainvoke({"messages": [{"role": "user", "content": prompt}]})
        report = result.get("structured_response")
        if not isinstance(report, RagAgentReport):
            report = RagAgentReport.model_validate(report)
        return {
            "rag_report": report.model_dump(mode="json"),
            "agents_used": [*state.get("agents_used", []), "policy_rag_agent"],
        }

    async def run_case_agent(state: AssistantState) -> dict[str, Any]:
        decision = SupervisorDecision.model_validate(state["decision"])
        prompt = (
            f"Supervisor task: {decision.case_task or 'Apply the relevant structured rules.'}\n"
            f"Original request: {_latest_user_text(state)}\n"
            f"Selected synthetic employee ID: {state.get('employee_id') or 'not supplied'}\n"
            f"As-of date: {state.get('as_of_date')}\n"
            f"Policy Agent report: {_safe_json(state.get('rag_report'))}"
        )
        result = await case_agent.ainvoke({"messages": [{"role": "user", "content": prompt}]})
        report = result.get("structured_response")
        if not isinstance(report, CaseAgentReport):
            report = CaseAgentReport.model_validate(report)
        return {
            "case_report": report.model_dump(mode="json"),
            "agents_used": [*state.get("agents_used", []), "employee_case_analyst"],
        }

    async def supervisor_final(state: AssistantState) -> dict[str, Any]:
        decision = SupervisorDecision.model_validate(state["decision"])
        prompt = (
            f"Original request: {_latest_user_text(state)}\n"
            f"Selected employee: {state.get('employee_id') or 'none'}\n"
            f"As-of date: {state.get('as_of_date')}\n"
            f"Route and rationale: {_safe_json(decision)}\n"
            f"Policy report: {_safe_json(state.get('rag_report'))}\n"
            f"Case report: {_safe_json(state.get('case_report'))}"
        )
        response = await synthesizer.ainvoke(
            [
                {"role": "system", "content": SUPERVISOR_SYNTHESIS_PROMPT},
                {"role": "user", "content": prompt},
            ]
        )
        return {
            "final_response": response.model_dump(mode="json"),
            "messages": [AIMessage(content=response.answer_markdown)],
        }

    async def escalation_response(state: AssistantState) -> dict[str, Any]:
        decision_data = state.get("decision")
        advice = None
        if decision_data:
            advice = SupervisorDecision.model_validate(decision_data).escalation
        if advice is None and state.get("safety_escalation"):
            advice = EscalationAdvice.model_validate(state["safety_escalation"])
        advice = advice or EscalationAdvice(
            category="legal_or_regulatory",
            severity="standard",
            reason="A qualified person needs to review this request.",
        )

        answer = escalation_answer(advice)
        response = FinalResponse(
            answer_markdown=answer,
            citations=[
                Citation(
                    policy_id="HR-SUPPORT-001",
                    section_number="4",
                    section_title="Mandatory human escalation",
                    source_path="data/policies/hr-support-escalation.md",
                    excerpt="Sensitive reports and employment decisions require human escalation.",
                )
            ],
            escalation_required=True,
            escalation_reason=advice.reason,
        )
        return {
            "final_response": response.model_dump(mode="json"),
            "messages": [AIMessage(content=answer)],
        }

    builder = StateGraph(AssistantState)
    builder.add_node("safety_gate", safety_gate)
    builder.add_node("supervisor_plan", supervisor_plan)
    builder.add_node("policy_rag_agent", run_rag_agent)
    builder.add_node("employee_case_analyst", run_case_agent)
    builder.add_node("supervisor_final", supervisor_final)
    builder.add_node("human_escalation", escalation_response)

    builder.add_edge(START, "safety_gate")
    builder.add_conditional_edges(
        "safety_gate",
        route_after_safety,
        {"plan": "supervisor_plan", "escalate": "human_escalation"},
    )
    builder.add_conditional_edges(
        "supervisor_plan",
        route_after_plan,
        {
            "rag": "policy_rag_agent",
            "case": "employee_case_analyst",
            "final": "supervisor_final",
            "escalate": "human_escalation",
        },
    )
    builder.add_conditional_edges(
        "policy_rag_agent",
        route_after_rag_report,
        {
            "case": "employee_case_analyst",
            "final": "supervisor_final",
        },
    )
    builder.add_edge("employee_case_analyst", "supervisor_final")
    builder.add_edge("supervisor_final", END)
    builder.add_edge("human_escalation", END)

    return builder.compile(checkpointer=checkpointer or InMemorySaver())


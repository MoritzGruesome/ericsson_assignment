from __future__ import annotations

import json
from collections.abc import AsyncIterator
from datetime import datetime
from uuid import uuid4
from zoneinfo import ZoneInfo

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage

from app.agents.models import CaseAgentReport, FinalResponse, SupervisorDecision
from app.config import Settings
from app.models.api import ChatRequest, ChatResponse, ExecutionStep, HealthResponse


router = APIRouter()


def _require_llm(settings: Settings) -> None:
    if not settings.openai_api_key:
        raise HTTPException(
            status_code=503,
            detail="OPENAI_API_KEY is not configured on the backend.",
        )


NODE_STEPS = {
    "safety_gate": ExecutionStep(
        kind="agent",
        name="safety_gate",
        label="Supervisor checked the request",
        agent="supervisor",
    ),
    "supervisor_plan": ExecutionStep(
        kind="agent",
        name="supervisor_plan",
        label="Supervisor selected a route",
        agent="supervisor",
    ),
    "supervisor_final": ExecutionStep(
        kind="agent",
        name="supervisor_final",
        label="Supervisor prepared the answer",
        agent="supervisor",
    ),
    "human_escalation": ExecutionStep(
        kind="agent",
        name="human_escalation",
        label="Supervisor applied the escalation policy",
        agent="supervisor",
    ),
}


def _execution_steps_for_update(node_name: str, update: object) -> list[ExecutionStep]:
    if node_name == "policy_rag_agent":
        tool_names = update.get("rag_tool_names", []) if isinstance(update, dict) else []
        tool_names = list(dict.fromkeys(tool_names)) or ["search_policies"]
        return [
            ExecutionStep(
                kind="tool",
                name=tool_name,
                label=f"Policy RAG Agent used {tool_name}",
                agent="policy_rag_agent",
            )
            for tool_name in tool_names
        ]

    if node_name == "employee_case_analyst":
        report_data = update.get("case_report") if isinstance(update, dict) else None
        report = CaseAgentReport.model_validate(report_data) if report_data else None
        tool_names = list(dict.fromkeys(report.tool_names_used)) if report else []
        if tool_names:
            return [
                ExecutionStep(
                    kind="tool",
                    name=tool_name,
                    label=f"Case Analyst used {tool_name}",
                    agent="employee_case_analyst",
                )
                for tool_name in tool_names
            ]
        return [
            ExecutionStep(
                kind="agent",
                name="employee_case_analyst",
                label="Case Analyst completed the analysis",
                agent="employee_case_analyst",
            )
        ]

    step = NODE_STEPS.get(node_name)
    return [step] if step else []


def _execution_history_from_state(state: dict) -> list[ExecutionStep]:
    history = [NODE_STEPS["safety_gate"]]
    decision_data = state.get("decision")
    if not decision_data:
        return [*history, NODE_STEPS["human_escalation"]]

    decision = SupervisorDecision.model_validate(decision_data)
    history.append(NODE_STEPS["supervisor_plan"])
    agents_used = state.get("agents_used", [])
    if "policy_rag_agent" in agents_used:
        history.extend(_execution_steps_for_update("policy_rag_agent", state))
    if "employee_case_analyst" in agents_used:
        history.extend(
            _execution_steps_for_update(
                "employee_case_analyst", {"case_report": state.get("case_report")}
            )
        )
    history.append(
        NODE_STEPS["human_escalation"]
        if decision.route == "escalate"
        else NODE_STEPS["supervisor_final"]
    )
    return history


def _to_chat_response(
    conversation_id: str,
    state: dict,
    execution_history: list[ExecutionStep] | None = None,
) -> ChatResponse:
    final = FinalResponse.model_validate(state["final_response"])
    decision_data = state.get("decision")
    route = SupervisorDecision.model_validate(decision_data).route if decision_data else "escalate"
    return ChatResponse(
        conversation_id=conversation_id,
        answer=final.answer_markdown,
        citations=final.citations,
        assumptions=final.assumptions,
        escalation_required=final.escalation_required,
        escalation_reason=final.escalation_reason,
        agents_used=list(dict.fromkeys(state.get("agents_used", ["supervisor"]))),
        route=route,
        execution_history=execution_history or _execution_history_from_state(state),
    )


def _graph_input(payload: ChatRequest, settings: Settings) -> dict:
    return {
        "messages": [HumanMessage(content=payload.message)],
        "employee_id": payload.employee_id,
        "as_of_date": (
            payload.as_of_date
            or datetime.now(ZoneInfo(settings.app_timezone)).date()
        ).isoformat(),
    }


@router.get("/health", response_model=HealthResponse)
async def health(request: Request) -> HealthResponse:
    settings: Settings = request.app.state.settings
    return HealthResponse(
        status="ok",
        llm_configured=bool(settings.openai_api_key),
        policy_index_path=str(settings.qdrant_path),
    )


@router.post("/chat", response_model=ChatResponse)
async def chat(payload: ChatRequest, request: Request) -> ChatResponse:
    settings: Settings = request.app.state.settings
    _require_llm(settings)
    conversation_id = payload.conversation_id or str(uuid4())
    config = {"configurable": {"thread_id": conversation_id}}
    graph = request.app.state.graph_service.get()
    try:
        state = await graph.ainvoke(_graph_input(payload, settings), config=config)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Assistant execution failed: {exc}") from exc
    return _to_chat_response(conversation_id, state)


@router.post("/chat/stream")
async def stream_chat(payload: ChatRequest, request: Request) -> StreamingResponse:
    settings: Settings = request.app.state.settings
    _require_llm(settings)
    conversation_id = payload.conversation_id or str(uuid4())
    config = {"configurable": {"thread_id": conversation_id}}
    graph = request.app.state.graph_service.get()

    async def events() -> AsyncIterator[str]:
        def emit(event: str, data: dict) -> str:
            return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"

        yield emit("start", {"conversation_id": conversation_id})
        execution_history: list[ExecutionStep] = []
        try:
            async for chunk in graph.astream(
                _graph_input(payload, settings), config=config, stream_mode="updates"
            ):
                for node_name, update in chunk.items():
                    for step in _execution_steps_for_update(node_name, update):
                        execution_history.append(step)
                        yield emit("progress", step.model_dump(mode="json"))
            final_state = await graph.aget_state(config)
            response = _to_chat_response(
                conversation_id,
                final_state.values,
                execution_history=execution_history,
            )
            yield emit("complete", response.model_dump(mode="json"))
        except Exception as exc:
            yield emit("error", {"message": str(exc)})

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


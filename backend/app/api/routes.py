from __future__ import annotations

import json
from collections.abc import AsyncIterator
from datetime import datetime
from uuid import uuid4
from zoneinfo import ZoneInfo

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage

from app.agents.models import FinalResponse, SupervisorDecision
from app.config import Settings
from app.models.api import ChatRequest, ChatResponse, HealthResponse


router = APIRouter()


def _require_llm(settings: Settings) -> None:
    if not settings.openai_api_key:
        raise HTTPException(
            status_code=503,
            detail="OPENAI_API_KEY is not configured on the backend.",
        )


def _to_chat_response(conversation_id: str, state: dict) -> ChatResponse:
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
        node_labels = {
            "safety_gate": "Supervisor is checking the request",
            "supervisor_plan": "Supervisor selected a route",
            "policy_rag_agent": "Policy agent searched the knowledge base",
            "employee_case_analyst": "Case analyst applied structured data",
            "supervisor_final": "Supervisor prepared the answer",
            "human_escalation": "Supervisor applied the escalation policy",
        }
        final_state = None
        try:
            async for chunk in graph.astream(
                _graph_input(payload, settings), config=config, stream_mode="updates"
            ):
                for node_name in chunk:
                    yield emit(
                        "progress",
                        {"node": node_name, "label": node_labels.get(node_name, node_name)},
                    )
            final_state = await graph.aget_state(config)
            response = _to_chat_response(conversation_id, final_state.values)
            yield emit("complete", response.model_dump(mode="json"))
        except Exception as exc:
            yield emit("error", {"message": str(exc)})

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


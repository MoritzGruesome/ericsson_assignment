from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.config import get_settings
from app.services.case_service import CaseDataService
from app.services.graph_service import AssistantGraphService
from app.services.policy_service import PolicySearchService


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    policy_service = PolicySearchService(settings)
    case_service = CaseDataService(
        settings.employee_data_path,
        settings.reference_data_path,
    )
    app.state.settings = settings
    app.state.policy_service = policy_service
    app.state.case_service = case_service
    app.state.graph_service = AssistantGraphService(
        settings=settings,
        policy_service=policy_service,
        case_service=case_service,
    )
    yield
    policy_service.close()


settings = get_settings()
app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Multi-agent HR policy assistant demo",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
app.include_router(router, prefix=settings.api_prefix)


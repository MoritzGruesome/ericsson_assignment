from __future__ import annotations

from threading import Lock

from langgraph.checkpoint.memory import InMemorySaver

from app.agents.graph import build_graph
from app.config import Settings
from app.services.case_service import CaseDataService
from app.services.policy_service import PolicySearchService


class AssistantGraphService:
    """Builds the OpenAI-backed graph lazily after configuration has been validated."""

    def __init__(
        self,
        *,
        settings: Settings,
        policy_service: PolicySearchService,
        case_service: CaseDataService,
    ) -> None:
        self.settings = settings
        self.policy_service = policy_service
        self.case_service = case_service
        self.checkpointer = InMemorySaver()
        self._graph = None
        self._lock = Lock()

    def get(self):
        if self._graph is None:
            with self._lock:
                if self._graph is None:
                    self._graph = build_graph(
                        settings=self.settings,
                        policy_service=self.policy_service,
                        case_service=self.case_service,
                        checkpointer=self.checkpointer,
                    )
        return self._graph


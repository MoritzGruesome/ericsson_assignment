from __future__ import annotations

from threading import Lock

from app.config import Settings
from app.models.rag import PolicySearchInput, PolicySearchResult
from app.rag.store import QdrantPolicyStore


class PolicySearchService:
    """Lazily initializes local embedding models and the Qdrant client."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._store: QdrantPolicyStore | None = None
        self._lock = Lock()

    @property
    def store(self) -> QdrantPolicyStore:
        if self._store is None:
            with self._lock:
                if self._store is None:
                    self._store = QdrantPolicyStore(
                        path=self.settings.qdrant_path,
                        collection_name=self.settings.policy_collection,
                        embedding_model_name=self.settings.openai_embedding_model,
                        openai_api_key=self.settings.openai_api_key,
                    )
        return self._store

    def search(self, request: PolicySearchInput) -> PolicySearchResult:
        return self.store.search(request)

    def close(self) -> None:
        if self._store is not None:
            self._store.close()


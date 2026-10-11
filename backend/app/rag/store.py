from __future__ import annotations

import re
from datetime import datetime, time, timezone
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

from langchain_openai import OpenAIEmbeddings
from qdrant_client import QdrantClient, models

from app.models.rag import PolicyChunk, PolicyEvidence, PolicySearchInput, PolicySearchResult


class PolicyIndexNotReadyError(RuntimeError):
    """Raised when policy search is attempted before ingestion."""


def _date_epoch(value) -> int:
    return int(datetime.combine(value, time.min, tzinfo=timezone.utc).timestamp())


class QdrantPolicyStore:
    def __init__(
        self,
        *,
        path: Path,
        collection_name: str,
        embedding_model_name: str,
        openai_api_key: str | None,
    ) -> None:
        if not openai_api_key:
            raise ValueError("OPENAI_API_KEY is required for policy embeddings.")
        path.mkdir(parents=True, exist_ok=True)
        self.client = QdrantClient(path=str(path))
        self.collection_name = collection_name
        self.embeddings = OpenAIEmbeddings(
            model=embedding_model_name,
            api_key=openai_api_key,
        )

    def rebuild(self, chunks: list[PolicyChunk]) -> int:
        if not chunks:
            raise ValueError("Cannot build an empty policy index")

        texts = [chunk.text for chunk in chunks]
        dense_vectors = self.embeddings.embed_documents(texts)

        if self.client.collection_exists(self.collection_name):
            self.client.delete_collection(self.collection_name)

        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=models.VectorParams(
                size=len(dense_vectors[0]),
                distance=models.Distance.COSINE,
            ),
        )

        points: list[models.PointStruct] = []
        for chunk, dense in zip(chunks, dense_vectors, strict=True):
            payload = chunk.model_dump(mode="json")
            payload["effective_date_epoch"] = _date_epoch(chunk.effective_date)
            points.append(
                models.PointStruct(
                    id=str(uuid5(NAMESPACE_URL, chunk.chunk_id)),
                    vector=dense,
                    payload=payload,
                )
            )

        self.client.upsert(collection_name=self.collection_name, points=points, wait=True)
        return len(points)

    def search(self, request: PolicySearchInput) -> PolicySearchResult:
        if not self.client.collection_exists(self.collection_name):
            raise PolicyIndexNotReadyError(
                "Policy index is missing. Run `python -m app.scripts.ingest_policies`."
            )

        dense = self.embeddings.embed_query(request.query)

        conditions: list[models.Condition] = [
            models.FieldCondition(
                key="document_status", match=models.MatchValue(value="active")
            ),
            models.FieldCondition(
                key="effective_date_epoch",
                range=models.Range(lte=_date_epoch(request.as_of_date)),
            ),
        ]
        applied_filters: dict[str, object] = {
            "document_status": "active",
            "effective_on_or_before": request.as_of_date.isoformat(),
        }

        if request.location:
            locations = ["global", request.location.lower()]
            conditions.append(
                models.FieldCondition(key="locations", match=models.MatchAny(any=locations))
            )
            applied_filters["locations"] = locations

        policy_ids = request.policy_ids or re.findall(
            r"\bHR-(?:[A-Z]+-)+\d{3}\b", request.query.upper()
        )
        if policy_ids:
            conditions.append(
                models.FieldCondition(
                    key="policy_id", match=models.MatchAny(any=policy_ids)
                )
            )
            applied_filters["policy_ids"] = policy_ids

        if request.employee_type:
            applicable_audiences = [
                request.employee_type,
                "all_employees",
                "all_workers",
                "employees",
                "eligible_employees",
            ]
            if request.employee_type == "permanent_employees":
                applicable_audiences.append("eligible_permanent_employees")
            conditions.append(
                models.FieldCondition(
                    key="applies_to",
                    match=models.MatchAny(any=applicable_audiences),
                )
            )
            applied_filters["employee_type"] = request.employee_type

        result = self.client.query_points(
            collection_name=self.collection_name,
            query=dense,
            query_filter=models.Filter(must=conditions),
            with_payload=True,
            limit=request.top_k,
        )

        evidence: list[PolicyEvidence] = []
        for point in result.points:
            payload = point.payload or {}
            evidence.append(
                PolicyEvidence(
                    chunk_id=str(payload["chunk_id"]),
                    policy_id=str(payload["policy_id"]),
                    policy_title=str(payload["policy_title"]),
                    section_number=str(payload["section_number"]),
                    section_title=str(payload["section_title"]),
                    text=str(payload["text"]),
                    source_path=str(payload["source_path"]),
                    effective_date=payload["effective_date"],
                    score=float(point.score),
                )
            )

        return PolicySearchResult(
            query=request.query,
            applied_filters=applied_filters,
            evidence=evidence,
        )

    def close(self) -> None:
        self.client.close()


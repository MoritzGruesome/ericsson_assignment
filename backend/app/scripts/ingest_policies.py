from __future__ import annotations

from app.config import REPOSITORY_ROOT, get_settings
from app.rag.parser import load_policy_chunks
from app.rag.store import QdrantPolicyStore


def main() -> None:
    settings = get_settings()
    chunks = load_policy_chunks(settings.policy_directory, REPOSITORY_ROOT)
    store = QdrantPolicyStore(
        path=settings.qdrant_path,
        collection_name=settings.policy_collection,
        embedding_model_name=settings.openai_embedding_model,
        openai_api_key=settings.openai_api_key,
    )
    try:
        count = store.rebuild(chunks)
    finally:
        store.close()
    print(f"Indexed {count} policy chunks in '{settings.policy_collection}'.")


if __name__ == "__main__":
    main()


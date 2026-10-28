from __future__ import annotations

from src.config import Settings
from src.retrieval.vector_store import get_vector_store


def retrieve_documents(settings: Settings, query: str, top_k: int = 4) -> list[dict]:
    store = get_vector_store(settings.storage_dir, settings.embedding_model)
    return store.query(query, top_k=top_k)

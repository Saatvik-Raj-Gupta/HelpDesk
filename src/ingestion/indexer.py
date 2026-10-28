from __future__ import annotations

import logging
import time
from dataclasses import dataclass

from src.config import Settings
from src.ingestion.chunking import chunk_documents
from src.ingestion.loaders import load_documents
from src.retrieval.vector_store import get_vector_store

logger = logging.getLogger(__name__)


@dataclass
class IndexResult:
    indexed_documents: int
    indexed_chunks: int
    errors: list[str]
    collection_name: str


def get_index_status(settings: Settings) -> IndexResult:
    store = get_vector_store(settings.storage_dir, settings.embedding_model)
    return IndexResult(
        indexed_documents=0,
        indexed_chunks=store.count(),
        errors=[],
        collection_name=store.collection_name,
    )


def index_knowledge_base(settings: Settings, *, force: bool = False) -> IndexResult:
    store = get_vector_store(settings.storage_dir, settings.embedding_model)
    if not force and store.count() > 0:
        logger.info("Knowledge-base index already exists; skipping ingestion. collection=%s chunks=%d", store.collection_name, store.count())
        return IndexResult(
            indexed_documents=0,
            indexed_chunks=store.count(),
            errors=[],
            collection_name=store.collection_name,
        )

    started_at = time.perf_counter()
    documents, errors = load_documents(settings.knowledge_base_dir)
    chunks = chunk_documents(documents, chunk_size=500, chunk_overlap=80)
    indexed_chunks = store.upsert_chunks(chunks)
    elapsed_ms = (time.perf_counter() - started_at) * 1000
    logger.info(
        "Knowledge-base indexing completed: docs=%d chunks=%d elapsed_ms=%.1f",
        len(documents),
        indexed_chunks,
        elapsed_ms,
    )
    return IndexResult(
        indexed_documents=len(documents),
        indexed_chunks=indexed_chunks,
        errors=errors,
        collection_name=store.collection_name,
    )

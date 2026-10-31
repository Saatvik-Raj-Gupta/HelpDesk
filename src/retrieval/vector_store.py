from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any, Callable

import chromadb
from sentence_transformers import SentenceTransformer

from src.ingestion.chunking import DocumentChunk

try:
    import streamlit as st
except ImportError:  # pragma: no cover - non-Streamlit execution
    st = None

logger = logging.getLogger(__name__)


def _cache_resource(func: Callable[..., Any]) -> Callable[..., Any]:
    if st is not None:
        return st.cache_resource(func)
    return func


@_cache_resource
def get_embedding_model(model_name: str) -> SentenceTransformer:
    started_at = time.perf_counter()
    model = SentenceTransformer(model_name)
    elapsed_ms = (time.perf_counter() - started_at) * 1000
    logger.info("Embedding model initialized: model=%s elapsed_ms=%.1f", model_name, elapsed_ms)
    return model


@_cache_resource
def get_vector_store(storage_dir: str | Path, embedding_model: str) -> "VectorStore":
    started_at = time.perf_counter()
    store = VectorStore(storage_dir, embedding_model)
    elapsed_ms = (time.perf_counter() - started_at) * 1000
    logger.info("Vector store initialized: path=%s elapsed_ms=%.1f", str(Path(storage_dir)), elapsed_ms)
    return store


class VectorStore:
    def __init__(self, storage_dir: str | Path, embedding_model: str) -> None:
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.collection_name = "helpdesk_knowledge"
        self.client = chromadb.PersistentClient(path=str(self.storage_dir))
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        self.embedding_model = embedding_model
        self.encoder = get_embedding_model(embedding_model)

    def embed(self, text: str) -> list[float]:
        embedding = self.encoder.encode(text, convert_to_numpy=True)
        return embedding.astype(float).tolist()

    def upsert_chunks(self, chunks: list[DocumentChunk]) -> int:
        if not chunks:
            return 0
        ids = [chunk.chunk_id for chunk in chunks]
        documents = [chunk.content for chunk in chunks]
        metadatas = [
            {
                "doc_id": chunk.doc_id,
                "source_name": chunk.source_name,
                "chunk_index": chunk.metadata.get("chunk_index", 0),
                "source_path": chunk.metadata.get("source_path", ""),
            }
            for chunk in chunks
        ]
        started_at = time.perf_counter()
        self.collection.upsert(ids=ids, documents=documents, metadatas=metadatas)
        elapsed_ms = (time.perf_counter() - started_at) * 1000
        logger.info("Document indexing complete: chunks=%d elapsed_ms=%.1f", len(chunks), elapsed_ms)
        return len(chunks)

    def remove_documents_not_in(self, active_doc_ids: set[str]) -> int:
        existing = self.collection.get(include=["metadatas"])
        ids = existing.get("ids", [])
        metadatas = existing.get("metadatas", [])
        stale_ids = [
            chunk_id
            for chunk_id, metadata in zip(ids, metadatas)
            if metadata and metadata.get("doc_id") not in active_doc_ids
        ]
        if stale_ids:
            self.collection.delete(ids=stale_ids)
        return len(stale_ids)

    def count(self) -> int:
        try:
            return self.collection.count()
        except Exception:  # pragma: no cover - runtime safeguard
            return 0

    def query(
        self,
        query: str,
        top_k: int = 4,
        relevance_threshold: float | None = None,
    ) -> list[dict[str, Any]]:
        query_vector = self.embed(query)
        results = self.collection.query(
            query_embeddings=[query_vector],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )

        hits: list[dict[str, Any]] = []
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        for document, metadata, distance in zip(documents, metadatas, distances):
            score = max(0.0, 1.0 - float(distance))
            if relevance_threshold is not None and score < relevance_threshold:
                continue
            hits.append(
                {
                    "source_name": metadata.get("source_name", "unknown"),
                    "doc_id": metadata.get("doc_id", "unknown"),
                    "content": document,
                    "score": round(score, 4),
                    "metadata": metadata,
                }
            )
        return hits

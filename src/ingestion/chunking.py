from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.ingestion.loaders import KnowledgeDocument


@dataclass
class DocumentChunk:
    chunk_id: str
    doc_id: str
    source_name: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)


def chunk_document(document: KnowledgeDocument, chunk_size: int = 500, chunk_overlap: int = 80) -> list[DocumentChunk]:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than zero")
    if chunk_overlap < 0:
        raise ValueError("chunk_overlap must be zero or greater")
    if chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be smaller than chunk_size")

    text = document.content
    if not text.strip():
        return []

    words = text.split()
    if len(words) <= chunk_size:
        return [
            DocumentChunk(
                chunk_id=f"{document.doc_id}::chunk_0",
                doc_id=document.doc_id,
                source_name=document.source_name,
                content=text,
                metadata={**document.metadata, "chunk_index": 0},
            )
        ]

    step = chunk_size - chunk_overlap
    chunks: list[DocumentChunk] = []
    for index in range(0, len(words), step):
        segment = words[index : index + chunk_size]
        if not segment:
            continue
        chunk_text = " ".join(segment)
        chunks.append(
            DocumentChunk(
                chunk_id=f"{document.doc_id}::chunk_{index // step}",
                doc_id=document.doc_id,
                source_name=document.source_name,
                content=chunk_text,
                metadata={**document.metadata, "chunk_index": index // step},
            )
        )
        if index + chunk_size >= len(words):
            break
    return chunks


def chunk_documents(documents: list[KnowledgeDocument], chunk_size: int = 500, chunk_overlap: int = 80) -> list[DocumentChunk]:
    chunks: list[DocumentChunk] = []
    for document in documents:
        chunks.extend(chunk_document(document, chunk_size=chunk_size, chunk_overlap=chunk_overlap))
    return chunks

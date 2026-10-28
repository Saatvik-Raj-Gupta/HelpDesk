from __future__ import annotations

from pathlib import Path

from src.config import Settings
from src.ingestion.chunking import chunk_documents
from src.ingestion.loaders import load_documents
from src.ingestion.indexer import index_knowledge_base


def test_load_documents_reads_markdown(tmp_path: Path) -> None:
    doc = tmp_path / "sample.md"
    doc.write_text("# Sample\n\nThis is a test document.", encoding="utf-8")

    documents, errors = load_documents(tmp_path)

    assert len(documents) == 1
    assert documents[0].source_name == "sample.md"
    assert errors == []


def test_chunk_documents_create_stable_ids(tmp_path: Path) -> None:
    doc = tmp_path / "sample.txt"
    doc.write_text("word " * 100, encoding="utf-8")

    documents, _ = load_documents(tmp_path)
    chunks = chunk_documents(documents, chunk_size=25, chunk_overlap=5)

    assert chunks
    assert chunks[0].chunk_id.endswith("::chunk_0")
    assert chunks[1].chunk_id.endswith("::chunk_1")


def test_index_knowledge_base_creates_chunks(tmp_path: Path, monkeypatch) -> None:
    knowledge_dir = tmp_path / "kb"
    knowledge_dir.mkdir()
    (knowledge_dir / "sample.md").write_text("# Header\n\nJava dependency missing class issue.", encoding="utf-8")

    settings = Settings(
        APP_ENV="test",
        STREAMLIT_SERVER_PORT=8501,
        LLM_PROVIDER="gemini",
        GEMINI_MODEL="gemini-3.8-flash",
        EMBEDDING_MODEL="sentence-transformers/all-MiniLM-L6-v2",
        GEMINI_API_KEY="demo-key",
        KNOWLEDGE_BASE_DIR=str(knowledge_dir),
        STORAGE_DIR=str(tmp_path / "chroma"),
        EVALUATION_DIR=str(tmp_path / "eval"),
    )

    result = index_knowledge_base(settings)

    assert result.indexed_documents == 1
    assert result.indexed_chunks >= 1
    assert result.collection_name == "helpdesk_knowledge"

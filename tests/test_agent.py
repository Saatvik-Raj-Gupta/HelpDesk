from __future__ import annotations

from pathlib import Path

from src.agent.graph import run_agent_workflow
from src.config import Settings


def test_run_agent_workflow_classifies_and_retrieves(tmp_path: Path) -> None:
    knowledge_dir = tmp_path / "kb"
    knowledge_dir.mkdir()
    (knowledge_dir / "dependency.md").write_text(
        "# Dependency troubleshooting\n\nAfter upgrading a Java dependency, the application fails to start because of a missing class.\n",
        encoding="utf-8",
    )

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

    result = run_agent_workflow(
        "After upgrading a Java dependency, the application fails to start because of a missing class.",
        settings=settings,
    )

    assert result["classification"]["category"] == "dependency_or_security"
    assert result["retrieval_required"] is True
    assert result["tool_activity"]
    assert result["answer"]["issue_summary"]

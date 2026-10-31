from __future__ import annotations

from pathlib import Path

import pytest

from src.config import Settings
from src.evaluation.dataset import EvaluationCase, load_evaluation_cases
from src.evaluation.evaluator import evaluate_cases
from src.agent.graph import workflow
from src.ingestion.indexer import index_knowledge_base
from src.llm_provider import GeminiProvider
from src.retrieval.vector_store import get_vector_store
from src.retrieval.retriever import retrieve_documents
from src.services.answer_generator import build_grounded_answer
from src.agent.tools import get_ticket_details
from src.triage.schemas import TicketClassification


def _settings(tmp_path: Path, knowledge_dir: Path) -> Settings:
    return Settings(
        APP_ENV="test",
        STREAMLIT_SERVER_PORT=8501,
        LLM_PROVIDER="gemini",
        GEMINI_MODEL="gemini-3.8-flash",
        EMBEDDING_MODEL="sentence-transformers/all-MiniLM-L6-v2",
        GEMINI_API_KEY="test-key",
        KNOWLEDGE_BASE_DIR=str(knowledge_dir),
        STORAGE_DIR=str(tmp_path / "chroma"),
        EVALUATION_DIR=str(tmp_path / "evaluation"),
        RETRIEVAL_SCORE_THRESHOLD=0.45,
    )


def test_evaluation_dataset_has_required_shape() -> None:
    cases = load_evaluation_cases("data/evaluation/sample_tickets.json")
    assert len(cases) == 10
    assert len({case.case_id for case in cases}) == 10
    assert sum(case.expected_category == "dependency_or_security" for case in cases) == 2
    assert sum(case.expected_category == "api_or_integration" for case in cases) == 2
    assert sum(case.expected_category == "deployment_or_runtime" for case in cases) == 2


def test_evaluation_reports_failures_and_non_perfect_denominators(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    knowledge_dir = tmp_path / "kb"
    knowledge_dir.mkdir()
    settings = _settings(tmp_path, knowledge_dir)
    monkeypatch.setattr(
        "src.evaluation.evaluator.index_knowledge_base",
        lambda settings, force: type("Result", (), {"errors": []})(),
    )
    cases = [
        EvaluationCase("case-1", "ticket", "other", [], False, True),
    ]

    report = evaluate_cases(
        settings,
        cases,
        classifier=lambda ticket: type("Classification", (), {"category": "other"})(),
        retriever=lambda settings, query, top_k: [],
        answer_builder=build_grounded_answer,
        workflow_runner=lambda ticket, settings: {},
    )

    assert report.metrics["category_accuracy"] == 1.0
    assert report.metrics["expected_source_retrieval_rate"] is None
    assert report.metrics["citation_validity"] is None
    assert report.metrics["unsupported_question_safety"] == 1.0
    assert report.failures == []


def test_invalid_citation_and_retrieval_failure_are_reported(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    knowledge_dir = tmp_path / "kb"
    knowledge_dir.mkdir()
    settings = _settings(tmp_path, knowledge_dir)
    monkeypatch.setattr(
        "src.evaluation.evaluator.index_knowledge_base",
        lambda settings, force: type("Result", (), {"errors": []})(),
    )
    case = EvaluationCase("case-1", "ticket", "other", ["known.md"], True, False)

    report = evaluate_cases(
        settings,
        [case],
        classifier=lambda ticket: type("Classification", (), {"category": "other"})(),
        retriever=lambda settings, query, top_k: (_ for _ in ()).throw(RuntimeError("retrieval down")),
        answer_builder=lambda query, passages: {
            "citations": [{"source": "missing.md", "content": "not retrieved"}],
            "human_review_recommended": True,
        },
        workflow_runner=lambda ticket, settings: {},
    )

    reasons = " ".join(report.failures[0].failures)
    assert "Retrieval failed" in reasons
    assert "Invalid citation" in reasons


def test_deleted_document_chunks_are_removed_on_reindex(tmp_path: Path) -> None:
    knowledge_dir = tmp_path / "kb"
    knowledge_dir.mkdir()
    old_document = knowledge_dir / "old.md"
    old_document.write_text("Old document with a unique legacy database phrase.", encoding="utf-8")
    settings = _settings(tmp_path, knowledge_dir)

    first = index_knowledge_base(settings, force=True)
    assert first.indexed_chunks == 1
    old_document.unlink()
    current = index_knowledge_base(settings, force=True)
    assert current.indexed_chunks == 0
    assert get_vector_store(settings.storage_dir, settings.embedding_model).count() == 0


def test_empty_ticket_and_provider_error_are_controlled(monkeypatch: pytest.MonkeyPatch) -> None:
    with pytest.raises(ValueError):
        get_ticket_details("")

    provider = GeminiProvider(api_key="test-key", model="test-model")
    monkeypatch.setattr(provider, "_get_client", lambda: (_ for _ in ()).throw(TimeoutError("timeout")))
    result = provider.health_check()
    assert result["ok"] is False
    assert "timeout" in result["message"]


def test_invalid_category_is_rejected_and_workflow_limit_is_enforced() -> None:
    with pytest.raises(ValueError):
        TicketClassification(
            category="not-a-category",
            priority="P4",
            short_issue_summary="invalid",
            confidence_explanation="invalid",
        )

    with pytest.raises(Exception, match="recursion"):
        workflow.invoke(
            {
                "ticket_text": "hello",
                "settings": None,
                "ticket_details": {},
                "classification": {},
                "retrieval_required": False,
                "retrieval_results": [],
                "answer": {},
                "tool_activity": [],
                "errors": [],
            },
            config={"recursion_limit": 1},
        )


def test_high_relevance_threshold_returns_no_context(tmp_path: Path) -> None:
    knowledge_dir = tmp_path / "kb"
    knowledge_dir.mkdir()
    (knowledge_dir / "known.md").write_text(
        "Java dependency version conflicts can cause missing classes at runtime.",
        encoding="utf-8",
    )
    settings = _settings(tmp_path, knowledge_dir)
    settings.retrieval_score_threshold = 0.99
    index_knowledge_base(settings, force=True)

    assert retrieve_documents(settings, "unrelated office printer issue", top_k=3) == []

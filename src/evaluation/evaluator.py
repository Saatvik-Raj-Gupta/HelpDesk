from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable

from src.agent.graph import run_agent_workflow
from src.config import Settings
from src.ingestion.indexer import index_knowledge_base
from src.retrieval.retriever import retrieve_documents
from src.services.answer_generator import build_grounded_answer
from src.triage.classifier import classify_ticket
from src.evaluation.dataset import EvaluationCase, load_evaluation_cases


@dataclass
class CaseResult:
    case_id: str
    expected: dict[str, Any]
    actual: dict[str, Any]
    failures: list[str]


@dataclass
class EvaluationReport:
    mode: str
    case_count: int
    metrics: dict[str, float | int | None]
    cases: list[CaseResult]
    indexing_errors: list[str]

    @property
    def failures(self) -> list[CaseResult]:
        return [case for case in self.cases if case.failures]

    def to_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "case_count": self.case_count,
            "metrics": self.metrics,
            "cases": [asdict(case) for case in self.cases],
            "indexing_errors": self.indexing_errors,
        }


def _rate(numerator: int, denominator: int) -> float | None:
    if denominator == 0:
        return None
    return round(numerator / denominator, 4)


def evaluate_cases(
    settings: Settings,
    cases: list[EvaluationCase],
    *,
    top_k: int = 3,
    mode: str = "stub",
    classifier: Callable[[str], Any] = classify_ticket,
    retriever: Callable[..., list[dict[str, Any]]] = retrieve_documents,
    answer_builder: Callable[[str, list[dict[str, Any]]], dict[str, Any]] = build_grounded_answer,
    workflow_runner: Callable[..., dict[str, Any]] = run_agent_workflow,
) -> EvaluationReport:
    index_result = index_knowledge_base(settings, force=True)
    case_results: list[CaseResult] = []
    category_correct = 0
    category_total = 0
    source_hits = 0
    source_total = 0
    citation_valid = 0
    citation_total = 0
    safety_correct = 0
    safety_total = 0
    workflow_terminated = 0

    for case in cases:
        failures: list[str] = []
        expected = {
            "category": case.expected_category,
            "sources": case.expected_sources,
            "answerable": case.answerable,
            "clarification_expected": case.clarification_expected,
        }
        actual: dict[str, Any] = {
            "category": None,
            "sources": [],
            "citations": [],
            "answerable_safety": None,
            "workflow_terminated": False,
        }

        try:
            classification = classifier(case.ticket)
            actual["category"] = classification.category
            category_total += 1
            if classification.category == case.expected_category:
                category_correct += 1
            else:
                failures.append(
                    f"Expected category {case.expected_category}, got {classification.category}."
                )
        except Exception as exc:
            failures.append(f"Classification failed: {exc}")

        try:
            passages = retriever(settings, case.ticket, top_k=top_k)
            actual["sources"] = sorted({item.get("source_name") for item in passages if item.get("source_name")})
            if case.expected_sources:
                source_total += 1
                if set(case.expected_sources).intersection(actual["sources"]):
                    source_hits += 1
                else:
                    failures.append("No expected source was retrieved.")
        except Exception as exc:
            passages = []
            failures.append(f"Retrieval failed: {exc}")
            if case.expected_sources:
                source_total += 1

        try:
            answer = answer_builder(case.ticket, passages)
            citations = answer.get("citations", [])
            actual["citations"] = citations
            retrieved_ids = {
                (item.get("source_name"), item.get("content", ""))
                for item in passages
            }
            for citation in citations:
                citation_source = citation.get("source")
                citation_content = citation.get("content", "")
                citation_total += 1
                if any(
                    citation_source == source and citation_content and citation_content in content
                    for source, content in retrieved_ids
                ):
                    citation_valid += 1
                else:
                    failures.append(f"Invalid citation: {citation!r}")

            safe_no_answer = (
                not case.answerable
                and not citations
                and answer.get("human_review_recommended") is True
            )
            actual["answerable_safety"] = safe_no_answer if not case.answerable else None
            if not case.answerable:
                safety_total += 1
                if safe_no_answer:
                    safety_correct += 1
                else:
                    failures.append("Unsupported case did not produce a safe no-answer response.")
        except Exception as exc:
            failures.append(f"Answer generation failed: {exc}")

        try:
            workflow_runner(case.ticket, settings=settings)
            actual["workflow_terminated"] = True
            workflow_terminated += 1
        except Exception as exc:
            failures.append(f"Workflow did not terminate successfully: {exc}")

        case_results.append(CaseResult(case.case_id, expected, actual, failures))

    metrics: dict[str, float | int | None] = {
        "category_accuracy": _rate(category_correct, category_total),
        "category_evaluated": category_total,
        "expected_source_retrieval_rate": _rate(source_hits, source_total),
        "expected_source_cases_evaluated": source_total,
        "citation_validity": _rate(citation_valid, citation_total),
        "citations_evaluated": citation_total,
        "unsupported_question_safety": _rate(safety_correct, safety_total),
        "unsupported_cases_evaluated": safety_total,
        "workflow_termination_rate": _rate(workflow_terminated, len(cases)),
    }
    return EvaluationReport(
        mode=mode,
        case_count=len(cases),
        metrics=metrics,
        cases=case_results,
        indexing_errors=index_result.errors,
    )


def evaluate_dataset(
    settings: Settings,
    dataset_path: str | Path,
    *,
    top_k: int = 3,
) -> EvaluationReport:
    return evaluate_cases(settings, load_evaluation_cases(dataset_path), top_k=top_k)

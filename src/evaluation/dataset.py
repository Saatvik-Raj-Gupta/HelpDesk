from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.triage.schemas import TicketCategory


@dataclass(frozen=True)
class EvaluationCase:
    case_id: str
    ticket: str
    expected_category: TicketCategory
    expected_sources: list[str]
    answerable: bool
    clarification_expected: bool


def load_evaluation_cases(path: str | Path) -> list[EvaluationCase]:
    records = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(records, list):
        raise ValueError("Evaluation dataset must contain a JSON list.")

    allowed_categories = set(TicketCategory.__args__)
    cases: list[EvaluationCase] = []
    seen_ids: set[str] = set()
    for record in records:
        if not isinstance(record, dict):
            raise ValueError("Each evaluation case must be a JSON object.")
        case_id = str(record.get("case_id", "")).strip()
        if not case_id or case_id in seen_ids:
            raise ValueError(f"Evaluation case IDs must be present and unique: {case_id!r}")
        category = record.get("expected_category")
        if category not in allowed_categories:
            raise ValueError(f"Unsupported expected category for {case_id}: {category!r}")
        ticket = str(record.get("ticket", "")).strip()
        if not ticket:
            raise ValueError(f"Evaluation ticket must not be empty: {case_id}")
        sources = record.get("expected_sources", [])
        if not isinstance(sources, list) or not all(isinstance(item, str) for item in sources):
            raise ValueError(f"expected_sources must be a list of strings: {case_id}")
        cases.append(
            EvaluationCase(
                case_id=case_id,
                ticket=ticket,
                expected_category=category,
                expected_sources=sources,
                answerable=bool(record.get("answerable", False)),
                clarification_expected=bool(record.get("clarification_expected", False)),
            )
        )
        seen_ids.add(case_id)
    return cases

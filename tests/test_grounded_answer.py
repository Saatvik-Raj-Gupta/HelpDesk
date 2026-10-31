from __future__ import annotations

from src.services.answer_generator import build_grounded_answer


def test_build_grounded_answer_returns_reasonable_output() -> None:
    passages = [
        {
            "source_name": "java_dependencies.md",
            "content": "A Java application may compile successfully but fail at runtime when resolved library versions do not match the APIs expected by the calling code.",
            "score": 0.92,
        }
    ]

    answer = build_grounded_answer("Java dependency mismatch", passages)

    assert answer["issue_summary"]
    assert answer["citations"]
    assert answer["human_review_recommended"] is True
    assert answer["suggested_diagnostic_steps"]

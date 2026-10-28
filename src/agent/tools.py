from __future__ import annotations

from typing import Any

from src.config import Settings, load_settings
from src.retrieval.retriever import retrieve_documents
from src.triage.classifier import determine_priority


def get_ticket_details(ticket: str) -> dict[str, Any]:
    if ticket is None or not str(ticket).strip():
        raise ValueError("Ticket text must not be empty.")

    normalized = str(ticket).strip()
    return {
        "ticket": normalized,
        "word_count": len(normalized.split()),
        "char_count": len(normalized),
        "is_blank": False,
    }


def search_knowledge_base(query: str, settings: Settings | None = None, top_k: int = 3) -> list[dict[str, Any]]:
    effective_settings = settings or load_settings()
    if not query or not str(query).strip():
        return []
    return retrieve_documents(effective_settings, str(query).strip(), top_k=top_k)


def calculate_priority(signals: str | dict[str, Any] | list[str]) -> str:
    if isinstance(signals, str):
        return determine_priority(signals)
    if isinstance(signals, dict):
        payload = " ".join(str(value) for value in signals.values())
        return determine_priority(payload)
    if isinstance(signals, list):
        return determine_priority(" ".join(str(value) for value in signals))
    return "P4"

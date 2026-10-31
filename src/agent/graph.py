from __future__ import annotations

from typing import Any, TypedDict

from langgraph.graph import END, StateGraph

from src.agent.tools import calculate_priority, get_ticket_details, search_knowledge_base
from src.config import Settings, load_settings
from src.ingestion.indexer import index_knowledge_base
from src.services.answer_generator import build_grounded_answer
from src.triage.classifier import classify_ticket


class WorkflowState(TypedDict):
    ticket_text: str
    settings: Settings
    ticket_details: dict[str, Any]
    classification: dict[str, Any]
    retrieval_required: bool
    retrieval_results: list[dict[str, Any]]
    answer: dict[str, Any]
    tool_activity: list[dict[str, Any]]
    errors: list[str]


def _record_tool(state: WorkflowState, tool_name: str, payload: dict[str, Any], *, ok: bool = True) -> None:
    state["tool_activity"].append({"tool": tool_name, "ok": ok, "payload": payload})


def _parse_ticket_node(state: WorkflowState) -> WorkflowState:
    try:
        details = get_ticket_details(state["ticket_text"])
        state["ticket_details"] = details
        _record_tool(state, "get_ticket_details", details)
    except Exception as exc:  # pragma: no cover - runtime guard
        state["errors"].append(str(exc))
        _record_tool(state, "get_ticket_details", {"error": str(exc)}, ok=False)
        raise
    return state


def _classify_ticket_node(state: WorkflowState) -> WorkflowState:
    try:
        classification = classify_ticket(state["ticket_text"])
        state["classification"] = classification.model_dump()
        priority = calculate_priority({"category": classification.category, "evidence": classification.evidence})
        state["classification"]["priority"] = priority
        _record_tool(state, "calculate_priority", {"category": classification.category, "priority": priority})
    except Exception as exc:  # pragma: no cover - runtime guard
        state["errors"].append(str(exc))
        _record_tool(state, "calculate_priority", {"error": str(exc)}, ok=False)
        raise
    return state


def _decide_retrieval_node(state: WorkflowState) -> WorkflowState:
    normalized = state["ticket_text"].strip().lower()
    greeting = normalized in {"hi", "hello", "hey", "good morning", "good afternoon"}
    if greeting:
        state["retrieval_required"] = False
        return state

    category = state["classification"].get("category", "other")
    state["retrieval_required"] = category != "other" or any(
        word in normalized for word in ["error", "timeout", "failed", "issue", "cannot", "login", "deploy", "database"]
    )
    return state


def _search_knowledge_base_node(state: WorkflowState) -> WorkflowState:
    if not state["retrieval_required"]:
        state["retrieval_results"] = []
        return state

    try:
        settings = state["settings"]
        result = index_knowledge_base(settings, force=False)
        if result.indexed_chunks == 0:
            state["errors"].append("No indexed knowledge-base chunks were found.")
        retrieval = search_knowledge_base(state["ticket_text"], settings=settings, top_k=3)
        state["retrieval_results"] = retrieval
        _record_tool(state, "search_knowledge_base", {"query": state["ticket_text"], "result_count": len(retrieval)})
    except Exception as exc:  # pragma: no cover - runtime guard
        state["errors"].append(str(exc))
        _record_tool(state, "search_knowledge_base", {"error": str(exc)}, ok=False)
        state["retrieval_results"] = []
    return state


def _build_answer_node(state: WorkflowState) -> WorkflowState:
    answer = build_grounded_answer(state["ticket_text"], state["retrieval_results"])
    state["answer"] = answer
    _record_tool(state, "build_grounded_answer", {"citations": len(answer.get("citations", []))})
    return state


builder = StateGraph(WorkflowState)
builder.add_node("parse_ticket", _parse_ticket_node)
builder.add_node("classify_ticket", _classify_ticket_node)
builder.add_node("decide_retrieval", _decide_retrieval_node)
builder.add_node("search_knowledge_base", _search_knowledge_base_node)
builder.add_node("build_answer", _build_answer_node)

builder.set_entry_point("parse_ticket")
builder.add_edge("parse_ticket", "classify_ticket")
builder.add_edge("classify_ticket", "decide_retrieval")
builder.add_conditional_edges(
    "decide_retrieval",
    lambda state: "search_knowledge_base" if state["retrieval_required"] else "build_answer",
    {"search_knowledge_base": "search_knowledge_base", "build_answer": "build_answer"},
)
builder.add_edge("search_knowledge_base", "build_answer")
builder.add_edge("build_answer", END)
workflow = builder.compile()


def run_agent_workflow(ticket_text: str, settings: Settings | None = None) -> dict[str, Any]:
    effective_settings = settings or load_settings()
    initial_state: WorkflowState = {
        "ticket_text": ticket_text,
        "settings": effective_settings,
        "ticket_details": {},
        "classification": {},
        "retrieval_required": False,
        "retrieval_results": [],
        "answer": {},
        "tool_activity": [],
        "errors": [],
    }
    result = workflow.invoke(initial_state, config={"recursion_limit": 6})
    return {
        "ticket_details": result.get("ticket_details", {}),
        "classification": result.get("classification", {}),
        "retrieval_required": result.get("retrieval_required", False),
        "retrieval_results": result.get("retrieval_results", []),
        "answer": result.get("answer", {}),
        "tool_activity": result.get("tool_activity", []),
        "errors": result.get("errors", []),
    }

from __future__ import annotations

import re

from src.triage.schemas import TicketClassification

CATEGORY_KEYWORDS = {
    "dependency_or_security": [
        "dependency",
        "security",
        "vulnerability",
        "cvss",
        "upgrade",
        "library",
        "package",
        "version",
        "missing class",
        "dependency conflict",
        "ssl",
        "certificate",
        "snyk",
    ],
    "api_or_integration": [
        "api",
        "integration",
        "webhook",
        "oauth",
        "rest",
        "graphql",
        "endpoint",
        "json",
        "timeout",
        "rate limit",
        "response code",
        "http 401",
        "http 500",
        "third party",
    ],
    "deployment_or_runtime": [
        "deploy",
        "deployment",
        "pod",
        "kubernetes",
        "container",
        "startup",
        "crash",
        "runtime",
        "service unavailable",
        "restart",
        "outage",
        "memory",
        "oom",
    ],
    "database": [
        "database",
        "db",
        "sql",
        "query",
        "connection",
        "timeout",
        "deadlock",
        "index",
        "migration",
        "postgres",
        "mysql",
    ],
    "access_or_authentication": [
        "login",
        "auth",
        "authentication",
        "access",
        "unauthorized",
        "forbidden",
        "session",
        "token",
        "permission",
        "403",
        "401",
        "single sign",
        "sso",
    ],
}

PRIORITY_HINTS = {
    "P1": [" outage ", "prod", "production down", "critical", "total outage", "security breach", "data loss"],
    "P2": ["urgent", "high priority", "cannot login", "api failing", "service unavailable", "restart loop"],
    "P3": ["degraded", "slow", "warning", "intermittent", "partial outage", "incident"],
    "P4": ["question", "how do i", "documentation", "minor", "low urgency", "investigation"],
}


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def _match_terms(text: str, keywords: list[str]) -> list[str]:
    matches: list[str] = []
    for keyword in keywords:
        if keyword in text:
            matches.append(keyword)
    return matches


def determine_priority(ticket_text: str) -> str:
    normalized = _normalize(ticket_text)
    for priority, hints in PRIORITY_HINTS.items():
        for hint in hints:
            if hint in normalized:
                return priority
    if re.search(r"\b(urgent|critical|down|outage|not working|failing)\b", normalized):
        return "P2"
    if re.search(r"\b(warn|warning|slow|intermittent)\b", normalized):
        return "P3"
    return "P4"


def classify_ticket(ticket_text: str) -> TicketClassification:
    if not ticket_text or not ticket_text.strip():
        raise ValueError("Ticket text must not be empty.")

    normalized = _normalize(ticket_text)
    category_scores: dict[str, int] = {category: 0 for category in CATEGORY_KEYWORDS}
    matched_terms: dict[str, list[str]] = {}

    for category, keywords in CATEGORY_KEYWORDS.items():
        matches = _match_terms(normalized, keywords)
        if matches:
            category_scores[category] = len(matches)
            matched_terms[category] = matches[:5]

    selected_category = max(category_scores.items(), key=lambda item: item[1])[0]
    if category_scores[selected_category] == 0:
        selected_category = "other"

    top_category = selected_category
    evidence = matched_terms.get(top_category, [])
    if not evidence:
        evidence = ["No explicit keyword match was found; classification relies on the overall ticket wording."]

    priority = determine_priority(ticket_text)
    summary = _build_summary(top_category, ticket_text, evidence)
    confidence = _build_confidence(top_category, category_scores, evidence)

    return TicketClassification(
        category=top_category,
        priority=priority,
        short_issue_summary=summary,
        evidence=evidence,
        confidence_explanation=confidence,
    )


def _build_summary(category: str, ticket_text: str, evidence: list[str]) -> str:
    trimmed = ticket_text.strip()
    if len(trimmed) > 120:
        preview = trimmed[:117].rstrip() + "..."
    else:
        preview = trimmed

    category_text = {
        "dependency_or_security": "dependency or security issue",
        "api_or_integration": "API or integration issue",
        "deployment_or_runtime": "deployment or runtime issue",
        "database": "database issue",
        "access_or_authentication": "access or authentication issue",
        "other": "general support issue",
    }[category]

    if evidence and evidence[0] != "No explicit keyword match was found; classification relies on the overall ticket wording.":
        return f"{category_text}: {evidence[0]} appears in the ticket."
    return f"{category_text}: {preview}"


def _build_confidence(category: str, category_scores: dict[str, int], evidence: list[str]) -> str:
    ranked = sorted(category_scores.items(), key=lambda item: item[1], reverse=True)
    best_score = ranked[0][1]
    second_score = ranked[1][1]
    if best_score == 0:
        return "No strong category signals were found. This classification is a low-confidence fallback based on the available wording only."
    if best_score > second_score:
        return f"The ticket strongly matches {category} based on explicit keywords and issue wording."
    return f"The ticket matches {category}, but the signal is not unique and may require a human review if more details are available."

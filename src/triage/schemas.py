from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

TicketCategory = Literal[
    "dependency_or_security",
    "api_or_integration",
    "deployment_or_runtime",
    "database",
    "access_or_authentication",
    "other",
]

TicketPriority = Literal["P1", "P2", "P3", "P4"]


class TicketClassification(BaseModel):
    category: TicketCategory
    priority: TicketPriority
    short_issue_summary: str = Field(min_length=1, max_length=250)
    evidence: list[str] = Field(default_factory=list)
    confidence_explanation: str = Field(min_length=1)

    model_config = {"extra": "forbid"}

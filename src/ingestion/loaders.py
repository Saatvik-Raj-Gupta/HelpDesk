from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

SUPPORTED_SUFFIXES = {".md", ".txt"}


@dataclass
class KnowledgeDocument:
    doc_id: str
    source_name: str
    path: str
    content: str
    metadata: dict[str, Any]


def _slugify(name: str) -> str:
    clean = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "-" for ch in name.lower())
    return clean.strip("-") or "document"


def load_documents(directory: str | Path) -> tuple[list[KnowledgeDocument], list[str]]:
    base_path = Path(directory)
    if not base_path.exists():
        return [], [f"Knowledge base directory does not exist: {base_path}"]

    documents: list[KnowledgeDocument] = []
    errors: list[str] = []

    for file_path in sorted(base_path.iterdir()):
        if not file_path.is_file():
            continue
        if file_path.suffix.lower() not in SUPPORTED_SUFFIXES:
            continue

        try:
            text = file_path.read_text(encoding="utf-8")
        except Exception as exc:  # pragma: no cover - exercised at runtime
            errors.append(f"Could not read {file_path.name}: {exc}")
            continue

        if not text.strip():
            errors.append(f"Skipped empty document: {file_path.name}")
            continue

        doc_id = _slugify(file_path.stem)
        documents.append(
            KnowledgeDocument(
                doc_id=doc_id,
                source_name=file_path.name,
                path=str(file_path),
                content=text.strip(),
                metadata={
                    "source_name": file_path.name,
                    "source_path": str(file_path),
                    "file_type": file_path.suffix.lower().lstrip("."),
                },
            )
        )

    return documents, errors

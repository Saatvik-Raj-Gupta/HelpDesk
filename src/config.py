from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from pydantic import BaseModel, Field, field_validator

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _coerce_optional_str(value: Any) -> str | None:
    if value is None:
        return None
    value = str(value).strip()
    return value or None


class Settings(BaseModel):
    app_name: str = "HelpDesk AI"
    app_environment: str = Field(default="development", alias="APP_ENV")
    streamlit_server_port: int = Field(default=8501, alias="STREAMLIT_SERVER_PORT")
    llm_provider: str = Field(default="gemini", alias="LLM_PROVIDER")
    gemini_model: str = Field(default="gemini-3.8-flash", alias="GEMINI_MODEL")
    embedding_model: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        alias="EMBEDDING_MODEL",
    )
    retrieval_score_threshold: float = Field(default=0.45, alias="RETRIEVAL_SCORE_THRESHOLD")
    gemini_api_key: str | None = Field(default=None, alias="GEMINI_API_KEY")
    knowledge_base_dir: str = Field(
        default=str(PROJECT_ROOT / "data" / "knowledge_base"),
        alias="KNOWLEDGE_BASE_DIR",
    )
    storage_dir: str = Field(
        default=str(PROJECT_ROOT / "storage" / "chroma"),
        alias="STORAGE_DIR",
    )
    evaluation_dir: str = Field(
        default=str(PROJECT_ROOT / "data" / "evaluation"),
        alias="EVALUATION_DIR",
    )

    model_config = {"populate_by_name": True}

    @property
    def llm_model(self) -> str:
        return self.gemini_model

    @field_validator("app_environment")
    @classmethod
    def validate_app_environment(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in {"development", "test", "production"}:
            raise ValueError("APP_ENV must be one of: development, test, production")
        return normalized

    @field_validator("llm_provider")
    @classmethod
    def validate_llm_provider(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in {"gemini", "google"}:
            raise ValueError("LLM_PROVIDER must be 'gemini' or 'google'")
        return "gemini" if normalized == "google" else normalized

    @field_validator("streamlit_server_port")
    @classmethod
    def validate_port(cls, value: int) -> int:
        if not 1 <= value <= 65535:
            raise ValueError("STREAMLIT_SERVER_PORT must be between 1 and 65535")
        return value

    @field_validator("retrieval_score_threshold")
    @classmethod
    def validate_retrieval_score_threshold(cls, value: float) -> float:
        if not 0.0 <= value <= 1.0:
            raise ValueError("RETRIEVAL_SCORE_THRESHOLD must be between 0 and 1")
        return value

    @field_validator("gemini_api_key", mode="before")
    @classmethod
    def validate_gemini_api_key(cls, value: Any) -> str | None:
        return _coerce_optional_str(value)

    @field_validator("knowledge_base_dir", "storage_dir", "evaluation_dir", mode="before")
    @classmethod
    def validate_path_strings(cls, value: Any) -> str:
        if value is None:
            return str(PROJECT_ROOT)
        return str(value).strip() or str(PROJECT_ROOT)


def _env_value(key: str) -> str | None:
    return _coerce_optional_str(os.getenv(key))


def load_settings() -> Settings:
    load_dotenv(PROJECT_ROOT / ".env", override=False)
    env_data = {
        "APP_ENV": _env_value("APP_ENV") or "development",
        "STREAMLIT_SERVER_PORT": _env_value("STREAMLIT_SERVER_PORT") or 8501,
        "LLM_PROVIDER": _env_value("LLM_PROVIDER") or "gemini",
        "GEMINI_MODEL": _env_value("GEMINI_MODEL") or "gemini-3.8-flash",
        "EMBEDDING_MODEL": _env_value("EMBEDDING_MODEL") or "sentence-transformers/all-MiniLM-L6-v2",
        "RETRIEVAL_SCORE_THRESHOLD": _env_value("RETRIEVAL_SCORE_THRESHOLD") or 0.45,
        "GEMINI_API_KEY": _env_value("GEMINI_API_KEY"),
        "KNOWLEDGE_BASE_DIR": _env_value("KNOWLEDGE_BASE_DIR") or str(PROJECT_ROOT / "data" / "knowledge_base"),
        "STORAGE_DIR": _env_value("STORAGE_DIR") or str(PROJECT_ROOT / "storage" / "chroma"),
        "EVALUATION_DIR": _env_value("EVALUATION_DIR") or str(PROJECT_ROOT / "data" / "evaluation"),
    }
    return Settings(**env_data)


def startup_checks(settings: Settings) -> dict[str, object]:
    status: dict[str, object] = {"ok": True, "warnings": [], "details": {}}
    details: dict[str, str] = {
        "APP_ENV": settings.app_environment,
        "LLM_PROVIDER": settings.llm_provider,
        "LLM_MODEL": settings.llm_model,
        "EMBEDDING_MODEL": settings.embedding_model,
        "KNOWLEDGE_BASE_DIR": settings.knowledge_base_dir,
        "STORAGE_DIR": settings.storage_dir,
    }
    status["details"] = details

    if settings.llm_provider == "gemini" and not settings.gemini_api_key:
        status["warnings"].append(
            "GEMINI_API_KEY is not set. The app can start in demo mode, but Gemini-backed generation is disabled until you add a key."
        )

    for path_name in ["knowledge_base_dir", "storage_dir", "evaluation_dir"]:
        path = Path(getattr(settings, path_name))
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            status["warnings"].append(f"Created missing directory: {path}")

    if status["warnings"]:
        status["ok"] = True

    return status

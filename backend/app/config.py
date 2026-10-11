from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Runtime settings loaded from environment variables and the repository .env."""

    model_config = SettingsConfigDict(
        env_file=REPOSITORY_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "PeopleGuide API"
    app_environment: str = "development"
    app_timezone: str = "Asia/Hong_Kong"
    api_prefix: str = "/api"

    openai_api_key: str | None = Field(default=None, repr=False)
    llm_model: str = "gpt-6-luna"
    llm_temperature: float = 0.0

    qdrant_path: Path = REPOSITORY_ROOT / ".data" / "qdrant"
    policy_collection: str = "peopleguide-policies"
    policy_directory: Path = REPOSITORY_ROOT / "data" / "policies"
    employee_data_path: Path = REPOSITORY_ROOT / "data" / "structured" / "employees.json"
    reference_data_path: Path = REPOSITORY_ROOT / "data" / "structured" / "reference-data.json"

    openai_embedding_model: str = "text-embedding-3-small"

    cors_origins: list[str] = ["http://localhost:5173"]

    @field_validator(
        "qdrant_path",
        "policy_directory",
        "employee_data_path",
        "reference_data_path",
        mode="before",
    )
    @classmethod
    def resolve_repository_path(cls, value):
        path = Path(value)
        return path if path.is_absolute() else REPOSITORY_ROOT / path


@lru_cache
def get_settings() -> Settings:
    return Settings()


"""
Configuration for the Personalized Outreach Architect.

Changes over the previous revision:

* ``database_url``, ``redis_url``, ``sendgrid_api_key``, ``from_email`` and
  ``from_name`` were required fields, so importing *any* module that touched
  settings raised without a full production environment. Nothing could be
  imported for a test. They are optional now, with a SQLite default for local
  use, and enforced at the boundary that needs them.
* ``LINKEDIN_EMAIL`` / ``LINKEDIN_PASSWORD`` are gone. The scraper that used
  them was non-functional and breached LinkedIn's User Agreement; enrichment is
  now a provider interface. See docs/data-sourcing.md.
* Adds an API key, so the endpoints -- including the one that sends mail -- are
  not open to anyone who can reach the port.
* Adds a production validator that refuses to start on an unsafe configuration.
"""

from __future__ import annotations

import json
import secrets
from pathlib import Path
from typing import Annotated, Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent
INSECURE_API_KEY = "changeme-in-production"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    # ---- LLM providers -----------------------------------------------------
    kimi_api_key: str | None = None
    kimi_base_url: str = "https://api.moonshot.cn/v1"
    kimi_model: str = "moonshot-v1-128k"

    deepseek_api_key: str | None = None
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"

    anthropic_api_key: str | None = None
    openai_api_key: str | None = None

    # ---- Data stores -------------------------------------------------------
    # SQLite by default so the project runs from a fresh clone. Point at
    # Postgres for anything beyond local use.
    database_url: str = Field(
        default_factory=lambda: f"sqlite:///{(BASE_DIR / 'outreach.db').as_posix()}"
    )
    redis_url: str = "redis://localhost:6379/0"

    # ---- Email -------------------------------------------------------------
    sendgrid_api_key: str | None = None
    from_email: str | None = None
    from_name: str | None = None

    # Refuse to actually deliver mail unless explicitly enabled. Sending is the
    # one irreversible action this service performs.
    email_sending_enabled: bool = False

    # ---- Enrichment --------------------------------------------------------
    # Ordered list of providers to consult. See enrichment/registry.py.
    enrichment_providers: Annotated[list[str], NoDecode] = Field(default_factory=lambda: ["manual"])

    # ---- External APIs -----------------------------------------------------
    newsapi_key: str | None = None
    serpapi_key: str | None = None

    # ---- Application -------------------------------------------------------
    api_key: str = INSECURE_API_KEY
    environment: Literal["development", "testing", "staging", "production"] = "development"
    log_level: str = "INFO"
    cors_allow_origins: Annotated[list[str], NoDecode] = Field(default_factory=list)
    max_concurrent_requests: int = 5
    rate_limit_per_minute: int = 10

    # ---- Agent behaviour ---------------------------------------------------
    min_personalization_score: float = 0.7
    max_retries: int = 3
    email_send_delay_seconds: int = 30

    # ---- Validators --------------------------------------------------------
    @field_validator("cors_allow_origins", "enrichment_providers", mode="before")
    @classmethod
    def _parse_list(cls, v):
        """Accept a comma-separated string or a JSON array from the environment."""
        if not isinstance(v, str):
            return v
        raw = v.strip()
        if not raw:
            return []
        if raw.startswith("["):
            try:
                parsed = json.loads(raw)
            except json.JSONDecodeError as exc:
                raise ValueError(f"expected a JSON array: {exc}") from exc
            return [str(x).strip() for x in parsed if str(x).strip()]
        return [x.strip() for x in raw.split(",") if x.strip()]

    @field_validator("log_level")
    @classmethod
    def _upper(cls, v: str) -> str:
        level = v.upper()
        if level not in {"CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"}:
            raise ValueError(f"invalid log_level: {v}")
        return level

    @model_validator(mode="after")
    def _guard_production(self) -> Settings:
        if self.environment == "production":
            self.validate_production_settings()
        return self

    # ---- Derived -----------------------------------------------------------
    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def has_insecure_api_key(self) -> bool:
        return self.api_key == INSECURE_API_KEY

    @property
    def enrichment_provider_list(self) -> list[str]:
        return self.enrichment_providers or ["manual"]

    # ---- Explicit checks ---------------------------------------------------
    def require_llm_credentials(self) -> None:
        if not any(
            (self.kimi_api_key, self.deepseek_api_key, self.anthropic_api_key, self.openai_api_key)
        ):
            raise RuntimeError(
                "No LLM provider configured. Set KIMI_API_KEY, DEEPSEEK_API_KEY, "
                "ANTHROPIC_API_KEY or OPENAI_API_KEY."
            )

    def require_email_credentials(self) -> None:
        """Called before any send. Sending is irreversible."""
        if not self.email_sending_enabled:
            raise RuntimeError(
                "Email sending is disabled. Set EMAIL_SENDING_ENABLED=true to deliver mail."
            )
        missing = [
            name
            for name in ("sendgrid_api_key", "from_email", "from_name")
            if not getattr(self, name)
        ]
        if missing:
            raise RuntimeError(f"Email is enabled but these are unset: {missing}")

    def validate_production_settings(self) -> None:
        problems: list[str] = []

        if self.has_insecure_api_key:
            problems.append(
                "API_KEY is still the default placeholder. Generate one with: "
                'python -c "import secrets; print(secrets.token_urlsafe(32))"'
            )
        if not self.cors_allow_origins:
            problems.append(
                "CORS_ALLOW_ORIGINS is empty; the API would reject all browser origins."
            )
        if self.database_url.startswith("sqlite"):
            problems.append("DATABASE_URL is SQLite; use Postgres in production.")
        if self.email_sending_enabled and not (
            self.sendgrid_api_key and self.from_email and self.from_name
        ):
            problems.append(
                "EMAIL_SENDING_ENABLED is true but the SendGrid settings are incomplete."
            )

        if problems:
            raise ValueError("Invalid production configuration:\n  - " + "\n  - ".join(problems))


def generate_api_key() -> str:
    return secrets.token_urlsafe(32)


settings = Settings()

"""Configuración central de la aplicación usando pydantic-settings."""

from functools import lru_cache
from typing import Literal

ComputrabajoCountry = Literal["ar", "co", "mx", "pe", "cl"]

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Variables de entorno y configuración global."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── App ──────────────────────────────────────────
    app_name: str = "Findjob"
    app_env: Literal["development", "staging", "production"] = "development"
    debug: bool = False
    secret_key: str = Field(
        default="change-me-in-production-use-a-64-char-random-string",
        min_length=32,
        description="Clave secreta para JWT y sesiones",
    )

    # ── Database ─────────────────────────────────────
    database_url: str = Field(
        default="postgresql+asyncpg://findjob:findjob@localhost:5432/findjob",
        description="URL async de PostgreSQL (TCP o socket Unix)",
    )
    database_echo: bool = False
    database_pool_size: int = 10
    database_max_overflow: int = 20

    # ── Redis / Celery ───────────────────────────────
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/1"

    # ── Embeddings (Gemini API) ──────────────────────
    embedding_dimensions: int = 768
    embed_after_scrape: bool = True
    embedding_batch_size: int = 20
    embedding_max_desc_chars: int = 8000
    embedding_task_type: str = "RETRIEVAL_DOCUMENT"
    embedding_request_delay: float = 0.5

    # ── Gemini ───────────────────────────────────────
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"
    gemini_embedding_model: str = "models/gemini-embedding-001"

    # ── Scraping ─────────────────────────────────────
    scraper_user_agent: str = (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    scraper_request_delay: float = 2.0
    scraper_headless: bool = True
    scraper_max_results: int = 30
    scraper_page_timeout_ms: int = 25_000
    scraper_fetch_details: bool = True
    scraper_detail_delay: float = 1.5
    scraper_detail_timeout_ms: int = 20_000
    computrabajo_country: ComputrabajoCountry = "ar"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def is_development(self) -> bool:
        return self.app_env == "development"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def database_url_str(self) -> str:
        return self.database_url

    @computed_field  # type: ignore[prop-decorator]
    @property
    def computrabajo_base_url(self) -> str:
        return f"https://{self.computrabajo_country}.computrabajo.com"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def scraper_locale(self) -> str:
        locales = {"ar": "es-AR", "co": "es-CO", "mx": "es-MX", "pe": "es-PE", "cl": "es-CL"}
        return locales.get(self.computrabajo_country, "es")


@lru_cache
def get_settings() -> Settings:
    """Singleton cacheado de configuración."""
    return Settings()


settings = get_settings()
"""Modelos de fuentes de scraping y ejecuciones."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import (
    ScrapeRunStatus,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
    enum_column,
)

if TYPE_CHECKING:
    from app.models.offer import Offer


class Source(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Portal o sitio del que se extraen ofertas (Indeed, Computrabajo, etc.)."""

    __tablename__ = "sources"

    name: Mapped[str] = mapped_column(String(120), nullable=False)
    slug: Mapped[str] = mapped_column(String(80), unique=True, nullable=False, index=True)
    base_url: Mapped[str] = mapped_column(String(512), nullable=False)
    scraper_class: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Ruta Python al scraper, ej: app.scrapers.computrabajo.ComputrabajoScraper",
    )
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    config: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    # Relaciones
    scrape_runs: Mapped[list[ScrapeRun]] = relationship(
        back_populates="source",
        cascade="all, delete-orphan",
        order_by="ScrapeRun.started_at.desc()",
    )
    offers: Mapped[list[Offer]] = relationship(back_populates="source")

    def __repr__(self) -> str:
        return f"<Source slug={self.slug!r}>"


class ScrapeRun(Base, UUIDPrimaryKeyMixin):
    """Registro de cada ejecución de un scraper sobre una fuente."""

    __tablename__ = "scrape_runs"
    __table_args__ = (
        Index("ix_scrape_runs_source_status", "source_id", "status"),
        Index("ix_scrape_runs_started_at", "started_at"),
    )

    source_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sources.id", ondelete="CASCADE"),
        nullable=False,
    )
    status: Mapped[ScrapeRunStatus] = enum_column(
        ScrapeRunStatus,
        default=ScrapeRunStatus.PENDING,
        nullable=False,
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    offers_found: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    offers_new: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    offers_updated: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_: Mapped[dict[str, Any] | None] = mapped_column("metadata", JSONB, nullable=True)

    # Relaciones
    source: Mapped[Source] = relationship(back_populates="scrape_runs")

    def __repr__(self) -> str:
        return f"<ScrapeRun source_id={self.source_id} status={self.status.value}>"
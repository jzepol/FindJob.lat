"""Modelo de ofertas laborales."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, EMBEDDING_DIM
from app.models.base import (
    JobType,
    Modality,
    OfferStatus,
    Seniority,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
    enum_column,
)

if TYPE_CHECKING:
    from app.models.application import Application
    from app.models.company_report import CompanyReport
    from app.models.salary_report import SalaryReport
    from app.models.saved_offer import SavedOffer
    from app.models.source import Source


class Offer(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Oferta laboral normalizada con embedding para matching semántico."""

    __tablename__ = "offers"
    __table_args__ = (
        UniqueConstraint("fingerprint", name="uq_offers_fingerprint"),
        UniqueConstraint("source_id", "external_id", name="uq_offers_source_external"),
        Index("ix_offers_status_published", "status", "published_at"),
        Index("ix_offers_company", "company"),
        Index("ix_offers_location", "location"),
        Index("ix_offers_modality_job_type", "modality", "job_type"),
        Index("ix_offers_seniority", "seniority"),
        # Índice HNSW para búsqueda vectorial (se crea en migración Alembic)
    )

    source_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sources.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    external_id: Mapped[str] = mapped_column(String(255), nullable=False)
    fingerprint: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="Hash SHA-256 de campos clave para deduplicación cross-source",
    )

    # Campos normalizados
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    normalized_title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    company: Mapped[str] = mapped_column(String(255), nullable=False)
    normalized_company: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)

    modality: Mapped[Modality] = enum_column(Modality, default=Modality.UNKNOWN, nullable=False)
    job_type: Mapped[JobType] = enum_column(JobType, default=JobType.UNKNOWN, nullable=False)
    seniority: Mapped[Seniority] = enum_column(Seniority, default=Seniority.UNKNOWN, nullable=False)

    # Soft-delete lógico via status (REMOVED = eliminada)
    status: Mapped[OfferStatus] = enum_column(
        OfferStatus,
        default=OfferStatus.ACTIVE,
        nullable=False,
        index=True,
    )

    salary_min: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    salary_max: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    salary_currency: Mapped[str | None] = mapped_column(String(3), nullable=True)

    url: Mapped[str] = mapped_column(String(1024), nullable=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Embedding semántico (nullable hasta que se procese)
    embedding: Mapped[list[float] | None] = mapped_column(
        Vector(EMBEDDING_DIM),
        nullable=True,
    )

    raw_data: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    # Relaciones
    source: Mapped[Source] = relationship(back_populates="offers")
    saved_by: Mapped[list[SavedOffer]] = relationship(back_populates="offer")
    applications: Mapped[list[Application]] = relationship(back_populates="offer")
    salary_reports: Mapped[list[SalaryReport]] = relationship(back_populates="offer")
    company_reports: Mapped[list[CompanyReport]] = relationship(back_populates="offer")

    def __repr__(self) -> str:
        return f"<Offer {self.title!r} @ {self.company!r}>"

    @property
    def is_active(self) -> bool:
        return self.status == OfferStatus.ACTIVE
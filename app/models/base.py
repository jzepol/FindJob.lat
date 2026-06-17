"""Mixins, enums compartidos y utilidades para modelos ORM."""

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum as SAEnum, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column


# ── Enums de dominio ─────────────────────────────────────────────────────────


class Modality(str, enum.Enum):
    """Modalidad de trabajo."""

    REMOTE = "remote"
    HYBRID = "hybrid"
    ON_SITE = "on_site"
    UNKNOWN = "unknown"


class JobType(str, enum.Enum):
    """Tipo de contrato / jornada."""

    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    CONTRACT = "contract"
    FREELANCE = "freelance"
    INTERNSHIP = "internship"
    TEMPORARY = "temporary"
    UNKNOWN = "unknown"


class Seniority(str, enum.Enum):
    """Nivel de experiencia requerido."""

    INTERN = "intern"
    JUNIOR = "junior"
    MID = "mid"
    SENIOR = "senior"
    LEAD = "lead"
    DIRECTOR = "director"
    UNKNOWN = "unknown"


class OfferStatus(str, enum.Enum):
    """Estado de una oferta. REMOVED actúa como soft-delete lógico."""

    ACTIVE = "active"
    EXPIRED = "expired"
    FILLED = "filled"
    REMOVED = "removed"


class ApplicationStatus(str, enum.Enum):
    """Estado de una postulación del usuario."""

    DRAFT = "draft"
    APPLIED = "applied"
    INTERVIEW = "interview"
    OFFER = "offer"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


class AlertFrequency(str, enum.Enum):
    """Frecuencia de envío de alertas."""

    INSTANT = "instant"
    DAILY = "daily"
    WEEKLY = "weekly"


class ScrapeRunStatus(str, enum.Enum):
    """Estado de una ejecución de scraper."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


# ── Helpers para SAEnum ──────────────────────────────────────────────────────

def sa_enum_type(enum_cls: type[enum.Enum], *, create_constraint: bool = True) -> SAEnum:
    """Factory de tipo SAEnum reutilizable (columnas y ARRAY)."""
    return SAEnum(
        enum_cls,
        name=enum_cls.__name__.lower(),
        values_callable=lambda e: [m.value for m in e],
        native_enum=True,
        create_constraint=create_constraint,
    )


def enum_column(enum_cls: type[enum.Enum], **kwargs):  # noqa: ANN003
    """Crea una columna SAEnum con valores nativos de Python."""
    return mapped_column(sa_enum_type(enum_cls), **kwargs)


# ── Mixins reutilizables ─────────────────────────────────────────────────────


class UUIDPrimaryKeyMixin:
    """PK UUID v4 autogenerado."""

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )


class TimestampMixin:
    """created_at / updated_at con timezone."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
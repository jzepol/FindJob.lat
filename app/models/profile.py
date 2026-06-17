"""Modelo de perfil profesional del usuario."""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

from pgvector.sqlalchemy import Vector
from sqlalchemy import ForeignKey, Index, Numeric, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, EMBEDDING_DIM
from app.models.base import (
    Modality,
    Seniority,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
    enum_column,
    sa_enum_type,
)

if TYPE_CHECKING:
    from app.models.user import User


class Profile(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Perfil 1:1 con el usuario — CV, skills y preferencias de búsqueda."""

    __tablename__ = "profiles"
    __table_args__ = (
        Index("ix_profiles_seniority", "seniority"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )

    full_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    headline: Mapped[str | None] = mapped_column(String(300), nullable=True)

    cv_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    cv_embedding: Mapped[list[float] | None] = mapped_column(
        Vector(EMBEDDING_DIM),
        nullable=True,
        comment="Embedding del CV para matching semántico",
    )

    skills: Mapped[list[str] | None] = mapped_column(
        ARRAY(String(100)),
        nullable=True,
    )

    preferred_modalities: Mapped[list[Modality] | None] = mapped_column(
        ARRAY(sa_enum_type(Modality, create_constraint=False)),
        nullable=True,
    )
    preferred_locations: Mapped[list[str] | None] = mapped_column(
        ARRAY(String(100)),
        nullable=True,
    )
    min_salary: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    seniority: Mapped[Seniority | None] = enum_column(Seniority, nullable=True)

    # Relaciones
    user: Mapped[User] = relationship(back_populates="profile")

    def __repr__(self) -> str:
        return f"<Profile user_id={self.user_id} name={self.full_name!r}>"
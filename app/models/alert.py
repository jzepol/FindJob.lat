"""Alertas de búsqueda configuradas por el usuario."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import (
    AlertFrequency,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
    enum_column,
)

if TYPE_CHECKING:
    from app.models.user import User


class Alert(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Alerta con filtros JSON y frecuencia de notificación."""

    __tablename__ = "alerts"
    __table_args__ = (
        Index("ix_alerts_user_active", "user_id", "is_active"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    filters: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        comment="Filtros: keywords, location, modality, seniority, salary_min, etc.",
    )
    frequency: Mapped[AlertFrequency] = enum_column(
        AlertFrequency,
        default=AlertFrequency.DAILY,
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relaciones
    user: Mapped[User] = relationship(back_populates="alerts")

    def __repr__(self) -> str:
        return f"<Alert {self.name!r} user={self.user_id}>"
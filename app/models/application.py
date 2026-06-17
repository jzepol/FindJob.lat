"""Postulaciones del usuario a ofertas."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import (
    ApplicationStatus,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
    enum_column,
)

if TYPE_CHECKING:
    from app.models.offer import Offer
    from app.models.user import User


class Application(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Seguimiento de postulaciones del usuario."""

    __tablename__ = "applications"
    __table_args__ = (
        UniqueConstraint("user_id", "offer_id", name="uq_applications_user_offer"),
        Index("ix_applications_user_status", "user_id", "status"),
        Index("ix_applications_applied_at", "applied_at"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    offer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("offers.id", ondelete="CASCADE"),
        nullable=False,
    )

    status: Mapped[ApplicationStatus] = enum_column(
        ApplicationStatus,
        default=ApplicationStatus.DRAFT,
        nullable=False,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    applied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relaciones
    user: Mapped[User] = relationship(back_populates="applications")
    offer: Mapped[Offer] = relationship(back_populates="applications")

    def __repr__(self) -> str:
        return f"<Application user={self.user_id} offer={self.offer_id} status={self.status.value}>"
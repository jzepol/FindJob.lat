"""Historial de eventos de karma por usuario."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import KarmaEventType, TimestampMixin, UUIDPrimaryKeyMixin, enum_column

if TYPE_CHECKING:
    from app.models.user import User


class KarmaEvent(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Evento de karma — cada tipo se otorga una sola vez por usuario."""

    __tablename__ = "karma_events"
    __table_args__ = (
        UniqueConstraint("user_id", "event_type", name="uq_karma_user_event"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    event_type: Mapped[KarmaEventType] = enum_column(KarmaEventType, nullable=False)
    points: Mapped[int] = mapped_column(Integer, nullable=False)

    user: Mapped[User] = relationship(back_populates="karma_events")
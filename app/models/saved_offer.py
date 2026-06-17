"""Ofertas guardadas por el usuario (favoritos)."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.offer import Offer
    from app.models.user import User


class SavedOffer(Base, UUIDPrimaryKeyMixin):
    """Relación usuario ↔ oferta guardada."""

    __tablename__ = "saved_offers"
    __table_args__ = (
        UniqueConstraint("user_id", "offer_id", name="uq_saved_offers_user_offer"),
        Index("ix_saved_offers_user_saved_at", "user_id", "saved_at"),
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
    saved_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relaciones
    user: Mapped[User] = relationship(back_populates="saved_offers")
    offer: Mapped[Offer] = relationship(back_populates="saved_by")

    def __repr__(self) -> str:
        return f"<SavedOffer user={self.user_id} offer={self.offer_id}>"
"""Reportes de salario (crowdsourced) vinculados a ofertas."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.offer import Offer
    from app.models.user import User


class SalaryReport(Base, UUIDPrimaryKeyMixin):
    """Reporte anónimo o autenticado de rango salarial."""

    __tablename__ = "salary_reports"
    __table_args__ = (
        Index("ix_salary_reports_offer", "offer_id"),
        Index("ix_salary_reports_reported_at", "reported_at"),
    )

    offer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("offers.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="Null = reporte anónimo",
    )

    salary_min: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    salary_max: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)

    reported_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relaciones
    offer: Mapped[Offer] = relationship(back_populates="salary_reports")
    user: Mapped[User | None] = relationship(back_populates="salary_reports")

    def __repr__(self) -> str:
        return f"<SalaryReport offer={self.offer_id} {self.salary_min}-{self.salary_max}>"
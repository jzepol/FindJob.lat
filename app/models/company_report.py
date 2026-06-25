"""Reportes de empresas — puestos fantasmas, alta rotación, etc."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import (
    CompanyReportStatus,
    CompanyReportType,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
    enum_column,
)

if TYPE_CHECKING:
    from app.models.offer import Offer
    from app.models.user import User


class CompanyReport(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Reporte de un usuario sobre una empresa u oferta."""

    __tablename__ = "company_reports"
    __table_args__ = (
        Index("ix_company_reports_company", "normalized_company"),
        Index("ix_company_reports_status", "status"),
        Index("ix_company_reports_user_company", "user_id", "normalized_company"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    offer_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("offers.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    normalized_company: Mapped[str] = mapped_column(String(255), nullable=False, index=True)

    report_type: Mapped[CompanyReportType] = enum_column(CompanyReportType, nullable=False)
    status: Mapped[CompanyReportStatus] = enum_column(
        CompanyReportStatus,
        default=CompanyReportStatus.PENDING,
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    user: Mapped[User] = relationship(back_populates="company_reports")
    offer: Mapped[Offer | None] = relationship(back_populates="company_reports")
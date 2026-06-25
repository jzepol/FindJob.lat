"""Modelo de usuarios."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.alert import Alert
    from app.models.application import Application
    from app.models.company_report import CompanyReport
    from app.models.karma_event import KarmaEvent
    from app.models.oauth_account import OAuthAccount
    from app.models.profile import Profile
    from app.models.saved_offer import SavedOffer
    from app.models.salary_report import SalaryReport


class User(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Cuenta de usuario autenticada."""

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    karma_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    profile: Mapped[Profile | None] = relationship(
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    oauth_accounts: Mapped[list[OAuthAccount]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    karma_events: Mapped[list[KarmaEvent]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    saved_offers: Mapped[list[SavedOffer]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    applications: Mapped[list[Application]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    alerts: Mapped[list[Alert]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    salary_reports: Mapped[list[SalaryReport]] = relationship(back_populates="user")
    company_reports: Mapped[list[CompanyReport]] = relationship(back_populates="user")

    def __repr__(self) -> str:
        return f"<User email={self.email!r} karma={self.karma_score}>"
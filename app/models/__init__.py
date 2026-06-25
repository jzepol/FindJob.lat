"""Modelos ORM — importar todos para que Alembic los detecte."""

from app.core.database import Base
from app.models.alert import Alert
from app.models.application import Application
from app.models.base import (
    AlertFrequency,
    ApplicationStatus,
    CompanyReportStatus,
    CompanyReportType,
    JobType,
    KarmaEventType,
    Modality,
    OAuthProvider,
    OfferStatus,
    ScrapeRunStatus,
    Seniority,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)
from app.models.company_report import CompanyReport
from app.models.karma_event import KarmaEvent
from app.models.oauth_account import OAuthAccount
from app.models.offer import Offer
from app.models.profile import Profile
from app.models.salary_report import SalaryReport
from app.models.saved_offer import SavedOffer
from app.models.source import ScrapeRun, Source
from app.models.user import User

__all__ = [
    "Base",
    "UUIDPrimaryKeyMixin",
    "TimestampMixin",
    "Modality",
    "JobType",
    "Seniority",
    "OfferStatus",
    "ApplicationStatus",
    "AlertFrequency",
    "ScrapeRunStatus",
    "OAuthProvider",
    "CompanyReportType",
    "CompanyReportStatus",
    "KarmaEventType",
    "Source",
    "ScrapeRun",
    "Offer",
    "User",
    "Profile",
    "OAuthAccount",
    "KarmaEvent",
    "CompanyReport",
    "SavedOffer",
    "Application",
    "Alert",
    "SalaryReport",
]
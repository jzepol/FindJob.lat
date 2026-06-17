"""Modelos ORM — importar todos para que Alembic los detecte."""

from app.core.database import Base
from app.models.alert import Alert
from app.models.application import Application
from app.models.base import (
    AlertFrequency,
    ApplicationStatus,
    JobType,
    Modality,
    OfferStatus,
    ScrapeRunStatus,
    Seniority,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)
from app.models.offer import Offer
from app.models.profile import Profile
from app.models.salary_report import SalaryReport
from app.models.saved_offer import SavedOffer
from app.models.source import ScrapeRun, Source
from app.models.user import User

__all__ = [
    # Base
    "Base",

    # Mixins
    "UUIDPrimaryKeyMixin",
    "TimestampMixin",

    # Enums
    "Modality",
    "JobType",
    "Seniority",
    "OfferStatus",
    "ApplicationStatus",
    "AlertFrequency",
    "ScrapeRunStatus",

    # Modelos
    "Source",
    "ScrapeRun",
    "Offer",
    "User",
    "Profile",
    "SavedOffer",
    "Application",
    "Alert",
    "SalaryReport",
]

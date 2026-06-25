"""Schemas Pydantic para la API REST."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.base import (
    CompanyReportType,
    JobType,
    Modality,
    OfferStatus,
    OAuthProvider,
    Seniority,
)


class SourceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    slug: str
    name: str
    base_url: str


class CompanyWarningOut(BaseModel):
    company: str
    normalized_company: str
    verified_reports: int
    primary_issue: str
    breakdown: dict[str, int]
    severity: str
    message: str


class OfferSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    company: str
    location: str | None
    modality: Modality
    job_type: JobType
    seniority: Seniority
    status: OfferStatus
    salary_min: Decimal | None
    salary_max: Decimal | None
    salary_currency: str | None
    url: str
    published_at: datetime | None
    source: SourceOut
    created_at: datetime
    updated_at: datetime
    duplicate_count: int = 1
    company_warning: CompanyWarningOut | None = None


class OfferDetail(OfferSummary):
    normalized_title: str | None
    normalized_company: str | None
    description: str | None
    external_id: str
    has_embedding: bool = False
    duplicates: list[OfferSummary] = Field(default_factory=list)


class PaginatedOffers(BaseModel):
    items: list[OfferSummary]
    total: int
    page: int
    page_size: int
    pages: int


class StatsOut(BaseModel):
    active_offers: int
    companies: int
    sources: int
    with_salary: int


class EnumsOut(BaseModel):
    modality: list[str]
    job_type: list[str]
    seniority: list[str]
    offer_status: list[str]


class SalaryRoleOut(BaseModel):
    role: str
    seniority: Seniority
    count: int
    salary_min: Decimal | None
    salary_max: Decimal | None
    salary_avg: Decimal | None
    currency: str | None


# ── Auth ─────────────────────────────────────────────────────


class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str | None = Field(None, max_length=200)


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class TokenOut(BaseModel):
    access_token: str | None = None
    token_type: str = "bearer"


class OAuthExchangeIn(BaseModel):
    code: str = Field(min_length=10, max_length=2048)


class OAuthAccountOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    provider: OAuthProvider
    email: str | None
    display_name: str | None
    avatar_url: str | None


class ProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    full_name: str | None
    headline: str | None
    cv_text: str | None
    skills: list[str] | None
    preferred_locations: list[str] | None
    seniority: Seniority | None


class ProfileUpdateIn(BaseModel):
    full_name: str | None = Field(None, max_length=200)
    headline: str | None = Field(None, max_length=300)
    cv_text: str | None = None
    skills: list[str] | None = None
    preferred_locations: list[str] | None = None
    seniority: Seniority | None = None


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    is_verified: bool
    karma_score: int
    profile: ProfileOut | None = None
    oauth_accounts: list[OAuthAccountOut] = Field(default_factory=list)


class KarmaOut(BaseModel):
    score: int
    min_to_report: int
    can_report: bool
    points_needed: int
    events: dict[str, int]


class CvUploadOut(BaseModel):
    cv_text: str
    chars: int
    filename: str
    karma_gained: int
    karma_score: int
    parsed_by: str = "gemini"
    embedding_ready: bool = False
    summary: str | None = None
    skills_extracted: list[str] = Field(default_factory=list)
    headline_extracted: str | None = None
    full_name_extracted: str | None = None


# ── Company reports ──────────────────────────────────────────


class CompanyReportIn(BaseModel):
    offer_id: UUID | None = None
    company_name: str = Field(min_length=2, max_length=255)
    report_type: CompanyReportType
    description: str | None = Field(None, max_length=2000)


class CompanyReportOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    company_name: str
    report_type: CompanyReportType
    status: str
    description: str | None
    created_at: datetime
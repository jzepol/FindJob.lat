"""Scraper de Remote OK — API JSON pública (sin Playwright)."""

from __future__ import annotations

import re
from datetime import datetime
from html import unescape
from typing import Any

import httpx
import structlog
from playwright.async_api import BrowserContext

from app.core.config import settings
from app.scrapers.base import BaseScraper
from app.scrapers.schemas import RawOffer, ScrapeParams
from app.services.normalizer import matches_keywords, normalize_text

logger = structlog.get_logger(__name__)

_API_URL = "https://remoteok.com/api"
_SPAM_FOOTER_RE = re.compile(
    r"Please mention the word.*$",
    re.IGNORECASE | re.DOTALL,
)
_HTML_TAG_RE = re.compile(r"<[^>]+>")


class RemoteOKScraper(BaseScraper):
    """Obtiene ofertas remotas desde la API de Remote OK."""

    slug = "remoteok"
    base_url = "https://remoteok.com"
    requires_browser = False

    async def search(
        self,
        params: ScrapeParams,
        context: BrowserContext | None,
    ) -> list[RawOffer]:
        max_results = params.max_results or settings.scraper_max_results
        raw_jobs = await self._fetch_api()
        offers: list[RawOffer] = []

        for job in raw_jobs:
            if not self._is_job_record(job):
                continue
            if params.keywords and params.keywords != "*" and not self._matches_search(job, params.keywords):
                continue
            if params.location and not self._matches_location(job, params.location):
                continue

            offers.append(self._to_raw_offer(job))
            if len(offers) >= max_results:
                break

        logger.info("remoteok_fetched", total=len(raw_jobs), matched=len(offers))
        return offers

    async def _fetch_api(self) -> list[dict[str, Any]]:
        headers = {
            "User-Agent": settings.scraper_user_agent,
            "Accept": "application/json",
        }
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            response = await client.get(_API_URL, headers=headers)
            response.raise_for_status()
            data = response.json()

        if not isinstance(data, list):
            return []
        return [item for item in data if isinstance(item, dict)]

    @staticmethod
    def _is_job_record(job: dict[str, Any]) -> bool:
        return bool(job.get("id") and job.get("position") and job.get("company"))

    def _matches_search(self, job: dict[str, Any], keywords: str) -> bool:
        tags = " ".join(job.get("tags") or [])
        blob = " ".join(
            [
                job.get("position", ""),
                job.get("company", ""),
                job.get("description", ""),
                tags,
            ]
        )
        return matches_keywords(blob, keywords)

    @staticmethod
    def _matches_location(job: dict[str, Any], location: str) -> bool:
        job_location = normalize_text(job.get("location") or "")
        return normalize_text(location) in job_location if job_location else False

    def _to_raw_offer(self, job: dict[str, Any]) -> RawOffer:
        job_id = str(job["id"])
        slug = str(job.get("slug") or job_id)
        url = str(job.get("url") or job.get("apply_url") or f"{self.base_url}/remote-jobs/{slug}")

        description = self._clean_description(str(job.get("description") or ""))
        tags: list[str] = list(job.get("tags") or [])
        salary_min = job.get("salary_min") or 0
        salary_max = job.get("salary_max") or 0

        salary_raw = None
        if salary_min and int(salary_min) > 0:
            if salary_max and int(salary_max) > int(salary_min):
                salary_raw = f"${salary_min} - ${salary_max} (USD)"
            else:
                salary_raw = f"${salary_min} (USD)"

        date_raw = job.get("date")
        posted_at_raw = None
        if date_raw:
            try:
                posted_at_raw = datetime.fromisoformat(str(date_raw).replace("Z", "+00:00")).isoformat()
            except ValueError:
                posted_at_raw = str(date_raw)

        location = (job.get("location") or "").strip() or "Remote"

        return RawOffer(
            title=str(job["position"]),
            company=str(job["company"]),
            location=location,
            url=url,
            external_id=job_id,
            description=description,
            posted_at_raw=posted_at_raw,
            modality_raw="remote",
            salary_raw=salary_raw,
            raw_data={
                "slug": slug,
                "tags": tags,
                "epoch": job.get("epoch"),
                "apply_url": job.get("apply_url"),
                "salary_min": salary_min,
                "salary_max": salary_max,
                "source": "remoteok_api",
            },
        )

    @staticmethod
    def _clean_description(html: str) -> str | None:
        if not html:
            return None
        text = unescape(html)
        text = _HTML_TAG_RE.sub("\n", text)
        text = _SPAM_FOOTER_RE.sub("", text)
        text = re.sub(r"\n{3,}", "\n\n", text).strip()
        return text or None
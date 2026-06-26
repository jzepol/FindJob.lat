"""Scraper de Bumeran Argentina — API searchV2 + Playwright para sesión."""

from __future__ import annotations

import json
import re
from typing import Any
from urllib.parse import parse_qs, urlparse

import structlog
from playwright.async_api import APIResponse, BrowserContext, Page

from app.core.config import settings
from app.scrapers.base import BaseScraper, polite_delay, with_page
from app.scrapers.schemas import RawOffer, ScrapeParams
from app.services.normalizer import clean_description

logger = structlog.get_logger(__name__)

_BASE_URL = "https://www.bumeran.com.ar"
_SEARCH_API = f"{_BASE_URL}/api/avisos/searchV2"
_SITE_ID = "BMAR"
_API_PAGE_SIZE = 20


class BumeranScraper(BaseScraper):
    """Busca ofertas en bumeran.com.ar vía API interna searchV2."""

    slug = "bumeran"
    base_url = _BASE_URL

    async def search(
        self,
        params: ScrapeParams,
        context: BrowserContext | None,
    ) -> list[RawOffer]:
        offers = await with_page(context, lambda page: self._search(page, params))

        if params.fetch_details and settings.scraper_fetch_details:
            await self._enrich_missing_descriptions(context, offers)

        return offers

    async def _search(self, page: Page, params: ScrapeParams) -> list[RawOffer]:
        listing_url = self._build_listing_url(params)
        max_results = params.max_results or settings.scraper_max_results
        body = self._build_search_body(params)

        session: dict[str, Any] = {"jwt": None, "pages": {}}

        def _page_index(url: str) -> int | None:
            qs = parse_qs(urlparse(url).query)
            raw = qs.get("page", ["0"])[0]
            try:
                return int(raw)
            except ValueError:
                return None

        async def on_request(request) -> None:
            if "searchV2" not in request.url:
                return
            jwt = request.headers.get("x-session-jwt")
            if jwt:
                session["jwt"] = jwt

        async def on_response(response) -> None:
            if "searchV2" not in response.url or response.request.method != "POST":
                return
            idx = _page_index(response.url)
            if idx is None or idx in session["pages"]:
                return
            try:
                session["pages"][idx] = await response.json()
            except Exception:
                pass

        page.on("request", on_request)
        page.on("response", on_response)

        def _is_search_v2(response) -> bool:
            return "searchV2" in response.url and response.request.method == "POST"

        try:
            async with page.expect_response(_is_search_v2, timeout=25_000):
                await page.goto(
                    listing_url,
                    wait_until="domcontentloaded",
                    timeout=settings.scraper_page_timeout_ms,
                )
        except Exception:
            if 0 not in session["pages"] and not session.get("jwt"):
                logger.warning("bumeran_searchv2_wait_timeout", url=listing_url)
                await page.wait_for_timeout(8_000)

        offers: list[RawOffer] = []
        page_num = 0
        api_headers = self._api_headers(listing_url, session.get("jwt"))

        while len(offers) < max_results:
            payload = session["pages"].get(page_num)
            if payload is None:
                if not api_headers.get("x-session-jwt"):
                    logger.warning("bumeran_missing_jwt", url=listing_url)
                    break
                payload = await self._fetch_api_page(
                    page,
                    page_num=page_num,
                    body=body,
                    listing_url=listing_url,
                    headers=api_headers,
                )
                if payload is None:
                    break

            batch = self._parse_api_response(payload)
            if not batch:
                break
            offers.extend(batch)

            if len(batch) < _API_PAGE_SIZE:
                break
            page_num += 1
            await polite_delay(0.4)

        total_available = None
        first_payload = session["pages"].get(0)
        if isinstance(first_payload, dict):
            total_available = first_payload.get("total")

        log_fn = logger.info if offers else logger.warning
        log_fn(
            "bumeran_api_fetched",
            url=listing_url,
            requested=max_results,
            count=len(offers[:max_results]),
            total_available=total_available,
            has_jwt=bool(session.get("jwt")),
        )
        return offers[:max_results]

    async def _fetch_api_page(
        self,
        page: Page,
        *,
        page_num: int,
        body: dict,
        listing_url: str,
        headers: dict[str, str],
    ) -> dict | None:
        api_url = f"{_SEARCH_API}?pageSize={_API_PAGE_SIZE}&page={page_num}&sort=RELEVANTES"
        response: APIResponse = await page.request.post(
            api_url,
            data=json.dumps(body),
            headers=headers,
        )
        if not response.ok:
            text = await response.text()
            logger.warning(
                "bumeran_api_error",
                status=response.status,
                url=api_url,
                detail=text[:200],
            )
            return None
        return await response.json()

    @staticmethod
    def _api_headers(listing_url: str, jwt: str | None) -> dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Referer": listing_url,
            "x-site-id": _SITE_ID,
            "Accept-Language": settings.scraper_locale,
        }
        if jwt:
            headers["x-session-jwt"] = jwt
        return headers

    async def _enrich_missing_descriptions(
        self,
        context: BrowserContext | None,
        offers: list[RawOffer],
    ) -> None:
        if context is None:
            return
        page = await context.new_page()
        try:
            for offer in offers:
                if offer.description:
                    continue
                try:
                    resp: APIResponse = await page.request.get(offer.url)
                    if not resp.ok:
                        continue
                    html = await resp.text()
                    if html:
                        offer.description = clean_description(html[:8000])
                except Exception as exc:
                    logger.warning("bumeran_detail_failed", url=offer.url, error=str(exc))
                await polite_delay(settings.scraper_detail_delay)
        finally:
            await page.close()

    def _parse_api_response(self, payload: dict) -> list[RawOffer]:
        content = payload.get("content")
        if not isinstance(content, list):
            return []
        return [self._api_item_to_raw(item) for item in content if isinstance(item, dict)]

    def _api_item_to_raw(self, item: dict) -> RawOffer:
        offer_id = item.get("id")
        title = (item.get("titulo") or "").strip()
        company = (item.get("empresa") or "—").strip()
        location = (item.get("localizacion") or "").strip() or None
        description = item.get("detalle")
        if description:
            description = clean_description(str(description))

        posted = item.get("fechaPublicacion") or item.get("fechaHoraPublicacion")
        modality = item.get("modalidadTrabajo")

        url = f"{_BASE_URL}/empleos/{offer_id}.html" if offer_id else _BASE_URL

        return RawOffer(
            title=title,
            company=company,
            location=location,
            url=url,
            external_id=str(offer_id) if offer_id is not None else title[:64],
            description=description,
            posted_at_raw=str(posted) if posted else None,
            modality_raw=str(modality) if modality else None,
            raw_data={**item, "country": "ar", "source": "searchV2"},
        )

    def _build_search_body(self, params: ScrapeParams) -> dict:
        keyword = (params.keywords or "").strip()
        if keyword and keyword.lower() not in ("*", "all"):
            return {"filtros": [], "query": keyword}
        return {
            "filtros": [{"id": "area", "value": "tecnologia-sistemas-y-telecomunicaciones"}],
        }

    @staticmethod
    def _build_listing_url(params: ScrapeParams) -> str:
        keyword = (params.keywords or "").strip().lower()
        if keyword and keyword not in ("*", "all"):
            slug = re.sub(r"[^a-z0-9]+", "-", keyword).strip("-")
            return f"{_BASE_URL}/empleos-busqueda-{slug}.html"
        return f"{_BASE_URL}/empleos-area-tecnologia-sistemas-y-telecomunicaciones.html"
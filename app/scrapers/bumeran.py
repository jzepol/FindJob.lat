"""Scraper de Bumeran Argentina — listado + detalle."""

from __future__ import annotations

import re

import structlog
from playwright.async_api import BrowserContext, Page
from urllib.parse import quote

from app.core.config import settings
from app.scrapers.base import BaseScraper, polite_delay, scroll_listing, with_page
from app.scrapers.schemas import RawOffer, ScrapeParams
from app.services.normalizer import clean_description, extract_bumeran_external_id

logger = structlog.get_logger(__name__)

_BASE_URL = "https://www.bumeran.com.ar"

_EXTRACT_LISTING_SCRIPT = """
({ maxResults }) => {
  const results = [];
  const seen = new Set();

  const links = Array.from(document.querySelectorAll('a[href*="/empleos/"]'))
    .filter((a) => (a.getAttribute("href") || "").endsWith(".html"));

  for (const anchor of links) {
    const href = (anchor.getAttribute("href") || "").split("#")[0];
    if (!href || seen.has(href)) continue;
    seen.add(href);

    const lines = anchor.innerText
      .split("\\n")
      .map((l) => l.trim())
      .filter(Boolean);

    if (lines.length < 2) continue;

    const dateLine = lines.find((l) => /actualizado|publicado|hace/i.test(l)) || null;
    const title = lines.find(
      (l) => l.length > 8 && !/actualizado|publicado|postulaci/i.test(l)
    ) || lines[1];
    const company = lines.find(
      (l, i) => i > 0 && l !== title && !/capital federal|remoto|buenos aires|postulaci|múltiples|discapacidad/i.test(l) && l.length < 80
    ) || "—";

    const location = lines.find((l) => /capital federal|buenos aires|córdoba|rosario|remoto/i.test(l)) || "";
    const modalityTags = lines.filter((l) => /^remoto$|^híbrido$|^hibrido$|^presencial$/i.test(l));

    results.push({
      title,
      company,
      location,
      url: href.startsWith("http") ? href : `https://www.bumeran.com.ar${href}`,
      postedAt: dateLine,
      modalityTags,
      salaryRaw: null,
    });

    if (results.length >= maxResults) break;
  }

  return results;
}
"""

_EXTRACT_DETAIL_SCRIPT = """
() => {
  const h1 = document.querySelector("h1")?.innerText?.trim() || "";
  const company =
    document.querySelector('a[href*="/perfiles/"], a[href*="/empresa"]')?.innerText?.trim() ||
    document.querySelector("[class*='employer'], [class*='company']")?.innerText?.trim() ||
    "";

  const body = document.body.innerText || "";
  const descMarker = "Descripción del puesto";
  let description = "";
  const idx = body.indexOf(descMarker);
  if (idx >= 0) {
    description = body.slice(idx + descMarker.length);
    const cutoffs = ["Empleos relacionados", "Postulación rápida", "Detalle del empleo"];
    for (const c of cutoffs) {
      const cidx = description.indexOf(c);
      if (cidx > 100) description = description.slice(0, cidx);
    }
  }

  const dateLine = body.match(/(Actualizado|Publicado)[^\\n]{0,40}/i)?.[0] || null;
  const location = body.match(/Buenos Aires[^\\n]{0,80}|Córdoba[^\\n]{0,80}|Rosario[^\\n]{0,80}/i)?.[0] || null;
  const modality = body.match(/\\b(Remoto|Híbrido|Hibrido|Presencial)\\b/i)?.[0] || null;

  const salaryMatch = body.match(/\\$\\s?[\\d.,]+(?:\\s*[-–]\\s*\\$\\s?[\\d.,]+)?/);

  return {
    h1,
    company,
    description: description.trim(),
    dateLine,
    location,
    modality,
    salaryRaw: salaryMatch ? salaryMatch[0] : null,
  };
}
"""


class BumeranScraper(BaseScraper):
    """Busca ofertas en bumeran.com.ar."""

    slug = "bumeran"
    base_url = _BASE_URL

    async def search(
        self,
        params: ScrapeParams,
        context: BrowserContext | None,
    ) -> list[RawOffer]:
        offers = await with_page(context, lambda page: self._scrape_listing(page, params))

        if params.fetch_details and settings.scraper_fetch_details:
            await self._enrich_with_details(context, offers)

        return offers

    async def _scrape_listing(self, page: Page, params: ScrapeParams) -> list[RawOffer]:
        url = self._build_search_url(params.keywords)
        max_results = params.max_results or settings.scraper_max_results

        await page.goto(url, wait_until="domcontentloaded", timeout=settings.scraper_page_timeout_ms)
        try:
            await page.wait_for_load_state("networkidle", timeout=10_000)
        except Exception:
            pass
        await page.wait_for_timeout(2_000)
        await scroll_listing(page)

        card_count = await page.locator('a[href*="/empleos/"]').count()
        logger.info("bumeran_listing_loaded", url=page.url, card_count=card_count)

        raw_items: list[dict] = await page.evaluate(
            _EXTRACT_LISTING_SCRIPT,
            {"maxResults": max_results},
        )
        return [self._item_to_raw_offer(item) for item in raw_items]

    async def _enrich_with_details(self, context: BrowserContext, offers: list[RawOffer]) -> None:
        page = await context.new_page()
        enriched = 0
        try:
            for offer in offers:
                try:
                    await self._fetch_detail(page, offer)
                    enriched += 1
                except Exception as exc:
                    logger.warning("bumeran_detail_failed", url=offer.url, error=str(exc))
                await polite_delay(settings.scraper_detail_delay)
        finally:
            await page.close()
        logger.info("bumeran_details_enriched", total=len(offers), enriched=enriched)

    async def _fetch_detail(self, page: Page, offer: RawOffer) -> None:
        await page.goto(offer.url, wait_until="domcontentloaded", timeout=settings.scraper_detail_timeout_ms)
        await page.wait_for_timeout(1_500)
        detail: dict = await page.evaluate(_EXTRACT_DETAIL_SCRIPT)

        if detail.get("description"):
            offer.description = clean_description(detail["description"])
        if detail.get("company") and offer.company in ("—", ""):
            offer.company = detail["company"]
        if detail.get("location"):
            offer.location = detail["location"]
        if detail.get("dateLine"):
            offer.posted_at_raw = detail["dateLine"]
        if detail.get("modality"):
            offer.modality_raw = detail["modality"]
        if detail.get("salaryRaw"):
            offer.salary_raw = detail["salaryRaw"]

        offer.raw_data = {**offer.raw_data, "detail": detail}

    def _item_to_raw_offer(self, item: dict) -> RawOffer:
        offer_url = item["url"]
        modality_tags: list[str] = item.get("modalityTags") or []

        return RawOffer(
            title=item["title"],
            company=item["company"],
            location=item.get("location") or None,
            url=offer_url,
            external_id=extract_bumeran_external_id(offer_url),
            posted_at_raw=item.get("postedAt"),
            modality_raw=", ".join(modality_tags) if modality_tags else None,
            salary_raw=item.get("salaryRaw"),
            raw_data={**item, "country": "ar"},
        )

    @staticmethod
    def _build_search_url(keywords: str) -> str:
        slug = re.sub(r"[^a-z0-9]+", "-", keywords.lower().strip()).strip("-")
        return f"{_BASE_URL}/empleos-busqueda-{slug}.html"
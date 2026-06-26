"""Scraper de Computrabajo — listado + detalle, configurable por país."""

from __future__ import annotations

import structlog
from playwright.async_api import BrowserContext, Page
from urllib.parse import urlencode

from app.core.config import settings
from app.scrapers.base import BaseScraper, polite_delay, scroll_listing, with_page
from app.scrapers.schemas import RawOffer, ScrapeParams
from app.services.normalizer import clean_description, extract_computrabajo_external_id

logger = structlog.get_logger(__name__)

_SEARCH_PATH = "/ofertas-de-trabajo/"
_CARD_SELECTORS = "article.box_offer, [class*='box_offer'], article[class*='offer']"

_EXTRACT_LISTING_SCRIPT = """
({ baseUrl, fallbackUrl, maxResults }) => {
  const results = [];

  let cards = Array.from(document.querySelectorAll("article.box_offer"));
  if (cards.length === 0) {
    cards = Array.from(document.querySelectorAll("article")).filter(
      (a) => a.querySelector("a.js-o-link, a[href*='/ofertas-de-trabajo/'], h2")
    );
  }
  if (cards.length === 0) {
    cards = Array.from(
      document.querySelectorAll("div.box_offer, div[class*='offer'], li[class*='offer']")
    );
  }

  cards.slice(0, maxResults).forEach((card) => {
    const titleEl = (
      card.querySelector("a.js-o-link") ||
      card.querySelector("a[href*='/ofertas-de-trabajo/']") ||
      card.querySelector("h2 a") ||
      card.querySelector("h3 a")
    );
    const title = titleEl?.textContent?.trim() || "";
    if (!title) return;

    const companyEl =
      card.querySelector("a[href*='/empresas/'], a.it-blank") ||
      card.querySelector("[class*='company'], [class*='Company'], [class*='empresa']");
    const company = companyEl?.textContent?.trim() || "—";

    const locEl =
      card.querySelector("p.fs16.fc_base.mt5:not(.dFlex) span.mr10") ||
      card.querySelector("p.fs16.mt5:not(.dFlex) span.mr10") ||
      card.querySelector("span.fs12, p.fs12") ||
      card.querySelector("[class*='ciudad']");
    const location = locEl?.textContent?.trim() || "";

    const dateEl = card.querySelector("p.fs13.fc_aux, span.date, time, [class*='date']");
    const postedAt = dateEl?.textContent?.trim() || null;

    const tagSpans = Array.from(card.querySelectorAll("div.fs13 span.dIB, div.fs13.mt15 span.dIB"));
    const modalityTags = [];
    const modalityIcons = [];
    let salaryRaw = null;

    tagSpans.forEach((span) => {
      const icon = span.querySelector("[class*='icon']");
      const text = span.textContent?.trim() || "";
      if (!text) return;
      if (icon?.className.includes("i_salary")) {
        salaryRaw = text;
        return;
      }
      if (icon && !icon.className.includes("i_salary")) {
        modalityTags.push(text);
        modalityIcons.push(icon.className);
      }
    });

    const href = (titleEl?.getAttribute("href") ?? "").split("#")[0];
    const url = href
      ? (href.startsWith("http") ? href : `${baseUrl}${href}`)
      : fallbackUrl;

    results.push({
      title,
      company,
      location,
      url,
      postedAt,
      modalityTags,
      modalityIcons,
      salaryRaw,
    });
  });

  return results;
}
"""

_EXTRACT_DETAIL_SCRIPT = """
() => {
  const headerTags = [];
  document.querySelectorAll(
    '.box_border.menu_top span.dIB, .box_border.menu_top .tag, .box_detail .tag'
  ).forEach((el) => {
    const text = (el.textContent || '').trim();
    if (text && text.length < 120 && !text.includes('Ocultas')) {
      headerTags.push(text);
    }
  });

  const metaItems = [];
  document.querySelectorAll('.box_detail li, .box_border li').forEach((li) => {
    const text = (li.textContent || '').trim().replace(/\\s+/g, ' ');
    if (text && text.length < 120 && !text.includes('%')) {
      metaItems.push(text);
    }
  });

  let description = '';
  const section = document.querySelector('.box_border.menu_top.dFlex, .box_border.menu_top');
  if (section) {
    description = section.innerText || '';
  }

  // Salario solo desde badges del header (evita ofertas similares en la página)
  const salaryRaw = headerTags.find((t) => t.includes('$'))
    || headerTags.find((t) => t.toLowerCase().includes('convenir'))
    || null;

  const experience = metaItems.find((t) => /años de experiencia|experiencia mínima/i.test(t)) || null;
  const education = metaItems.find((t) => /educación mínima|estudios mínimos/i.test(t)) || null;

  return {
    headerTags: [...new Set(headerTags)],
    metaItems: [...new Set(metaItems)],
    description,
    salaryRaw,
    experience,
    education,
  };
}
"""


class ComputrabajoScraper(BaseScraper):
    """Busca ofertas en computrabajo.com (un país por instancia / slug)."""

    def __init__(self, country: str | None = None) -> None:
        self._country = (country or settings.computrabajo_country).lower()

    @property
    def slug(self) -> str:
        return f"computrabajo-{self._country}"

    @property
    def base_url(self) -> str:
        return f"https://{self._country}.computrabajo.com"

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
        url = self._build_search_url(params.keywords, params.location)
        max_results = params.max_results or settings.scraper_max_results

        await page.goto(url, wait_until="domcontentloaded", timeout=settings.scraper_page_timeout_ms)
        try:
            await page.wait_for_load_state("networkidle", timeout=10_000)
        except Exception:
            pass
        await page.wait_for_timeout(2_000)

        try:
            await page.wait_for_selector(_CARD_SELECTORS, timeout=6_000)
        except Exception:
            pass
        await scroll_listing(page)

        card_count = await page.locator("article.box_offer, article[class*='offer']").count()
        logger.info(
            "computrabajo_listing_loaded",
            country=settings.computrabajo_country,
            url=page.url,
            card_count=card_count,
        )

        raw_items: list[dict] = await page.evaluate(
            _EXTRACT_LISTING_SCRIPT,
            {
                "baseUrl": self.base_url,
                "fallbackUrl": url,
                "maxResults": max_results,
            },
        )

        return [self._item_to_raw_offer(item) for item in raw_items]

    async def _enrich_with_details(self, context: BrowserContext, offers: list[RawOffer]) -> None:
        """Visita cada URL de detalle para extraer descripción y metadata."""
        page = await context.new_page()
        enriched = 0

        try:
            for offer in offers:
                try:
                    await self._fetch_detail(page, offer)
                    enriched += 1
                except Exception as exc:
                    logger.warning(
                        "detail_fetch_failed",
                        url=offer.url,
                        error=str(exc),
                    )
                await polite_delay(settings.scraper_detail_delay)
        finally:
            await page.close()

        logger.info("details_enriched", total=len(offers), enriched=enriched)

    async def _fetch_detail(self, page: Page, offer: RawOffer) -> None:
        await page.goto(offer.url, wait_until="domcontentloaded", timeout=settings.scraper_detail_timeout_ms)
        try:
            await page.wait_for_load_state("networkidle", timeout=8_000)
        except Exception:
            pass
        await page.wait_for_timeout(1_000)

        detail: dict = await page.evaluate(_EXTRACT_DETAIL_SCRIPT)

        description = clean_description(detail.get("description"))
        if description:
            offer.description = description

        detail_salary = detail.get("salaryRaw")
        if detail_salary:
            offer.salary_raw = detail_salary

        header_tags: list[str] = detail.get("headerTags") or []
        if header_tags and not offer.modality_raw:
            modality_tags = [
                t for t in header_tags
                if any(k in t.lower() for k in ("remoto", "presencial", "híbrido", "hibrido"))
            ]
            if modality_tags:
                offer.modality_raw = ", ".join(modality_tags)

        offer.raw_data = {
            **offer.raw_data,
            "detail": {
                "header_tags": header_tags,
                "meta_items": detail.get("metaItems") or [],
                "experience": detail.get("experience"),
                "education": detail.get("education"),
            },
        }

    def _item_to_raw_offer(self, item: dict) -> RawOffer:
        offer_url = item["url"]
        modality_tags: list[str] = item.get("modalityTags") or []
        modality_icons: list[str] = item.get("modalityIcons") or []

        return RawOffer(
            title=item["title"],
            company=item["company"],
            location=item.get("location") or None,
            url=offer_url,
            external_id=extract_computrabajo_external_id(offer_url),
            posted_at_raw=item.get("postedAt"),
            modality_raw=", ".join(modality_tags) if modality_tags else None,
            salary_raw=item.get("salaryRaw"),
            raw_data={
                **item,
                "modality_icons": modality_icons,
                "country": settings.computrabajo_country,
            },
        )

    def _build_search_url(self, keywords: str, location: str) -> str:
        query: dict[str, str] = {"q": keywords}
        if location:
            query["l"] = location
        return f"{self.base_url}{_SEARCH_PATH}?{urlencode(query)}"
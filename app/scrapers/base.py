"""Infraestructura Playwright compartida por todos los scrapers."""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from typing import Any

import structlog
from playwright.async_api import Browser, BrowserContext, Page, async_playwright

from app.core.config import settings
from app.scrapers.schemas import RawOffer, ScrapeParams

logger = structlog.get_logger(__name__)

# Script anti-detección portado de job-agent (simplificado para Chromium headless)
_STEALTH_INIT_SCRIPT = """
Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
Object.defineProperty(navigator, 'languages', { get: () => ['es-CO', 'es', 'en-US', 'en'] });
if (!window.chrome) {
  window.chrome = { runtime: {} };
}
"""


class BaseScraper(ABC):
    """Contrato común para scrapers por portal."""

    slug: str
    base_url: str
    requires_browser: bool = True

    @abstractmethod
    async def search(
        self,
        params: ScrapeParams,
        context: BrowserContext | None,
    ) -> list[RawOffer]:
        """Ejecuta búsqueda y devuelve ofertas crudas."""

    async def run(self, params: ScrapeParams) -> list[RawOffer]:
        """Ejecuta search con o sin browser según el scraper."""
        if self.requires_browser:
            async with browser_context() as context:
                offers = await self.search(params, context)
        else:
            offers = await self.search(params, None)

        logger.info(
            "scrape_completed",
            scraper=self.slug,
            keywords=params.keywords,
            location=params.location,
            count=len(offers),
        )
        return offers


@asynccontextmanager
async def browser_context() -> AsyncIterator[BrowserContext]:
    """Context manager de Playwright con configuración estándar."""
    async with async_playwright() as playwright:
        browser = await _launch_browser(playwright)
        context = await browser.new_context(
            user_agent=settings.scraper_user_agent,
            locale=settings.scraper_locale,
            viewport={"width": 1280, "height": 720},
            extra_http_headers={
                "Accept-Language": f"{settings.scraper_locale},es;q=0.9,en;q=0.8",
            },
        )
        await context.add_init_script(_STEALTH_INIT_SCRIPT)
        try:
            yield context
        finally:
            await context.close()
            await browser.close()


async def _launch_browser(playwright: Any) -> Browser:
    return await playwright.chromium.launch(
        headless=settings.scraper_headless,
        args=["--disable-blink-features=AutomationControlled"],
    )


async def with_page(context: BrowserContext, fn: Any) -> Any:
    """Abre una pestaña, ejecuta `fn(page)` y la cierra."""
    page = await context.new_page()
    try:
        return await fn(page)
    finally:
        await page.close()


async def polite_delay(seconds: float | None = None) -> None:
    """Rate limiting entre requests."""
    await asyncio.sleep(seconds or settings.scraper_request_delay)


async def scroll_listing(page: Page) -> None:
    """Scroll para revelar cards con lazy-load (patrón job-agent)."""
    await page.evaluate("window.scrollBy(0, 600)")
    await page.wait_for_timeout(600)
    await page.evaluate("window.scrollBy(0, 600)")
    await page.wait_for_timeout(400)
    await page.evaluate("window.scrollTo(0, 0)")
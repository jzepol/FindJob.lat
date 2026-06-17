"""Registro de scrapers disponibles por slug de Source."""

from __future__ import annotations

from app.scrapers.base import BaseScraper
from app.scrapers.bumeran import BumeranScraper
from app.scrapers.computrabajo import ComputrabajoScraper
from app.scrapers.remoteok import RemoteOKScraper

_REGISTRY: dict[str, type[BaseScraper]] = {
    "computrabajo": ComputrabajoScraper,
    "remoteok": RemoteOKScraper,
    "bumeran": BumeranScraper,
}


def get_scraper(slug: str) -> BaseScraper:
    """Instancia el scraper para un slug de fuente."""
    scraper_cls = _REGISTRY.get(slug)
    if scraper_cls is None:
        known = ", ".join(sorted(_REGISTRY))
        raise ValueError(f"Scraper desconocido: {slug!r}. Disponibles: {known}")
    return scraper_cls()


def scraper_class_path(slug: str) -> str:
    """Ruta Python del scraper (para Source.scraper_class)."""
    scraper_cls = _REGISTRY.get(slug)
    if scraper_cls is None:
        raise ValueError(f"Scraper desconocido: {slug!r}")
    return f"{scraper_cls.__module__}.{scraper_cls.__name__}"


def list_scrapers() -> list[str]:
    """Lista slugs de scrapers registrados."""
    return sorted(_REGISTRY)
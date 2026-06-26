"""Registro de scrapers disponibles por slug de Source."""

from __future__ import annotations

import os

from app.core.config import settings
from app.scrapers.base import BaseScraper
from app.scrapers.bumeran import BumeranScraper
from app.scrapers.computrabajo import ComputrabajoScraper
from app.scrapers.remoteok import RemoteOKScraper
from app.services.source_defaults import COMPUTRABAJO_COUNTRIES, all_scraper_slugs, computrabajo_slug

_REGISTRY: dict[str, type[BaseScraper]] = {
    "remoteok": RemoteOKScraper,
    "bumeran": BumeranScraper,
}


def _resolve_computrabajo_country(slug: str) -> str:
    if slug.startswith("computrabajo-"):
        return slug.split("-", 1)[1]
    return settings.computrabajo_country


def get_scraper(slug: str) -> BaseScraper:
    """Instancia el scraper para un slug de fuente."""
    if slug == "computrabajo" or slug.startswith("computrabajo-"):
        country = _resolve_computrabajo_country(slug)
        os.environ["COMPUTRABAJO_COUNTRY"] = country
        return ComputrabajoScraper(country=country)

    scraper_cls = _REGISTRY.get(slug)
    if scraper_cls is None:
        known = ", ".join(list_scrapers())
        raise ValueError(f"Scraper desconocido: {slug!r}. Disponibles: {known}")
    return scraper_cls()


def scraper_class_path(slug: str) -> str:
    """Ruta Python del scraper (para Source.scraper_class)."""
    if slug == "computrabajo" or slug.startswith("computrabajo-"):
        return "app.scrapers.computrabajo.ComputrabajoScraper"
    scraper_cls = _REGISTRY.get(slug)
    if scraper_cls is None:
        raise ValueError(f"Scraper desconocido: {slug!r}")
    return f"{scraper_cls.__module__}.{scraper_cls.__name__}"


def list_scrapers() -> list[str]:
    """Lista slugs de scrapers disponibles."""
    return all_scraper_slugs()
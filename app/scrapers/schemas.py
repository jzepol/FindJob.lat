"""DTOs compartidos entre scrapers y servicios de ingestión."""

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class RawOffer:
    """Oferta cruda extraída de un portal antes de normalizar."""

    title: str
    company: str
    url: str
    external_id: str
    location: str | None = None
    description: str | None = None
    posted_at_raw: str | None = None
    modality_raw: str | None = None
    salary_raw: str | None = None
    raw_data: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ScrapeParams:
    """Parámetros de búsqueda para un scraper."""

    keywords: str
    location: str = ""
    fetch_details: bool = True
    max_results: int | None = None


@dataclass(slots=True)
class IngestResult:
    """Resultado de persistir ofertas en la base de datos."""

    found: int = 0
    new: int = 0
    updated: int = 0
    embedded: int = 0
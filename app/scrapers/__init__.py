from app.scrapers.base import BaseScraper
from app.scrapers.bumeran import BumeranScraper
from app.scrapers.computrabajo import ComputrabajoScraper
from app.scrapers.remoteok import RemoteOKScraper
from app.scrapers.registry import get_scraper, list_scrapers
from app.scrapers.schemas import IngestResult, RawOffer, ScrapeParams

__all__ = [
    "BaseScraper",
    "ComputrabajoScraper",
    "RemoteOKScraper",
    "BumeranScraper",
    "RawOffer",
    "ScrapeParams",
    "IngestResult",
    "get_scraper",
    "list_scrapers",
]
"""Metadatos por slug de fuente (portal)."""

from __future__ import annotations

from collections.abc import Callable

COMPUTRABAJO_COUNTRIES: dict[str, str] = {
    "ar": "Argentina",
    "co": "Colombia",
    "mx": "México",
    "pe": "Perú",
    "cl": "Chile",
}


def computrabajo_slug(country: str) -> str:
    return f"computrabajo-{country.lower()}"


def defaults_for_slug(slug: str) -> dict[str, str]:
    if slug.startswith("computrabajo-"):
        code = slug.split("-", 1)[1]
        label = COMPUTRABAJO_COUNTRIES.get(code, code.upper())
        return {
            "name": f"Computrabajo {label}",
            "base_url": f"https://{code}.computrabajo.com",
        }
    fixed: dict[str, dict[str, str]] = {
        "computrabajo": {
            "name": "Computrabajo",
            "base_url": "https://ar.computrabajo.com",
        },
        "remoteok": {"name": "Remote OK", "base_url": "https://remoteok.com"},
        "bumeran": {"name": "Bumeran Argentina", "base_url": "https://www.bumeran.com.ar"},
    }
    if slug not in fixed:
        raise ValueError(f"Fuente desconocida: {slug!r}")
    return fixed[slug]


def all_scraper_slugs() -> list[str]:
    slugs = ["remoteok", "bumeran"]
    slugs.extend(computrabajo_slug(c) for c in COMPUTRABAJO_COUNTRIES)
    return sorted(slugs)
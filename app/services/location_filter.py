"""Normalización de filtros de ubicación para búsqueda."""

from __future__ import annotations

# Alias comunes → patrones SQL LIKE (sin acentos obligatorios)
_LOCATION_ALIASES: dict[str, list[str]] = {
    "bs": ["buenos aires", "gba", "caba", "capital federal"],
    "caba": ["caba", "capital federal", "buenos aires"],
    "gba": ["gba", "buenos aires"],
    "ba": ["buenos aires", "gba", "caba"],
    "cdmx": ["ciudad de mexico", "cdmx", "méxico df", "mexico df"],
    "df": ["ciudad de mexico", "cdmx"],
    "stgo": ["santiago", "r.metropolitana"],
    "sp": ["são paulo", "sao paulo"],
}

_MIN_LOCATION_LEN = 3


def location_like_patterns(raw: str | None) -> list[str] | None:
    """Devuelve patrones LIKE para filtrar ubicación, o None si es demasiado ambiguo."""
    if not raw or not raw.strip():
        return None

    loc = raw.strip().lower()
    if loc in _LOCATION_ALIASES:
        return [f"%{p}%" for p in _LOCATION_ALIASES[loc]]

    if len(loc) < _MIN_LOCATION_LEN:
        return None

    return [f"%{loc}%"]
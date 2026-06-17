"""Normalización de texto, fingerprints y parsing de campos de ofertas."""

from __future__ import annotations

import hashlib
import re
import unicodedata
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.models.base import JobType, Modality, Seniority

_WHITESPACE_RE = re.compile(r"\s+")
_COMPUTRABAJO_ID_RE = re.compile(r"/([a-zA-Z0-9][a-zA-Z0-9-]{4,})$")

# Iconos de modalidad en Computrabajo (AR/CO comparten clases)
_COMPUTRABAJO_ICON_MODALITY: dict[str, Modality] = {
    "i_home": Modality.REMOTE,
    "i_home_office": Modality.HYBRID,
    "i_office": Modality.ON_SITE,
    "i_building": Modality.ON_SITE,
}


def normalize_text(value: str | None) -> str:
    """Minúsculas, sin acentos, sin puntuación extra — para deduplicación."""
    if not value:
        return ""
    text = unicodedata.normalize("NFKD", value)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)
    return _WHITESPACE_RE.sub(" ", text).strip()


def make_fingerprint(
    *,
    title: str,
    company: str,
    location: str | None,
    source_slug: str,
    external_id: str,
) -> str:
    """SHA-256 para deduplicación — incluye external_id para evitar colisiones."""
    payload = "|".join(
        [
            source_slug,
            normalize_text(title),
            normalize_text(company),
            normalize_text(location),
            external_id.strip().lower(),
        ]
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def matches_keywords(text: str, keywords: str) -> bool:
    """True si todos los términos de keywords aparecen en text."""
    blob = normalize_text(text)
    terms = [normalize_text(term) for term in keywords.split() if term.strip()]
    if not terms:
        return True
    return all(term in blob for term in terms)


_BUMERAN_ID_RE = re.compile(r"-(\d+)\.html(?:\?.*)?$", re.IGNORECASE)


def extract_bumeran_external_id(url: str) -> str:
    """Extrae ID numérico final de URLs de Bumeran."""
    match = _BUMERAN_ID_RE.search(url.split("?")[0])
    if match:
        return match.group(1)
    return extract_computrabajo_external_id(url)


def extract_computrabajo_external_id(url: str) -> str:
    """Extrae un ID estable desde la URL de Computrabajo."""
    path = url.split("?")[0].rstrip("/")
    match = _COMPUTRABAJO_ID_RE.search(path)
    if match:
        return match.group(1)[:255]
    slug = path.rsplit("/", maxsplit=1)[-1]
    return slug[:255] if slug else hashlib.sha256(url.encode()).hexdigest()[:32]


def _modality_from_icons(icons: list[str] | None) -> Modality | None:
    """Mapea clases de icono de Computrabajo a Modality."""
    if not icons:
        return None
    # Ordenar claves de más específica a menos (i_home_office antes que i_home)
    ordered_keys = sorted(_COMPUTRABAJO_ICON_MODALITY, key=len, reverse=True)
    for icon_class in icons:
        for key in ordered_keys:
            if key in icon_class:
                return _COMPUTRABAJO_ICON_MODALITY[key]
    return None


def parse_modality(
    *texts: str | None,
    icons: list[str] | None = None,
    default: Modality = Modality.ON_SITE,
) -> Modality:
    """Infiere modalidad desde tags, título y iconos de Computrabajo."""
    icon_result = _modality_from_icons(icons)
    if icon_result is not None:
        return icon_result

    blob = normalize_text(" ".join(t for t in texts if t))
    if not blob:
        return default

    # Híbrido antes que remoto (ej: "presencial y remoto")
    hybrid_markers = (
        "presencial y remoto",
        "remoto y presencial",
        "hibrida",
        "hibrido",
        "hybrid",
        "mixto",
        "home office hibrido",
        "modalidad hibrida",
    )
    if any(marker in blob for marker in hybrid_markers):
        return Modality.HYBRID

    remote_markers = (
        "remoto",
        "remote",
        "teletrabajo",
        "home office",
        "trabajo remoto",
        "100 remoto",
        "desde casa",
        "en casa",
    )
    if any(marker in blob for marker in remote_markers):
        return Modality.REMOTE

    onsite_markers = (
        "presencial",
        "on site",
        "onsite",
        "en oficina",
        "oficina fisica",
    )
    if any(marker in blob for marker in onsite_markers):
        return Modality.ON_SITE

    return default


def parse_seniority(title: str, description: str | None = None) -> Seniority:
    """Heurística simple de seniority desde título/descripción."""
    blob = normalize_text(f"{title} {description or ''}")
    if any(k in blob for k in ("director", "head of", "vp ")):
        return Seniority.DIRECTOR
    if any(k in blob for k in ("lead", "lider", "tech lead")):
        return Seniority.LEAD
    if any(k in blob for k in ("senior", "sr ", " ssr")):
        return Seniority.SENIOR
    if any(k in blob for k in ("semi senior", "semisenior", "ssr")):
        return Seniority.MID
    if any(k in blob for k in ("junior", "jr ", "trainee", "practicante")):
        return Seniority.JUNIOR
    if any(k in blob for k in ("intern", "pasante", "becario")):
        return Seniority.INTERN
    return Seniority.UNKNOWN


def parse_job_type(*texts: str | None) -> JobType:
    """Infiere tipo de contrato desde texto libre (incluye tags de Computrabajo)."""
    blob = normalize_text(" ".join(t for t in texts if t))
    if not blob:
        return JobType.UNKNOWN
    if any(k in blob for k in ("tiempo parcial", "part time", "medio tiempo")):
        return JobType.PART_TIME
    if any(k in blob for k in ("freelance", "independiente")):
        return JobType.FREELANCE
    if any(
        k in blob
        for k in (
            "pasantia",
            "pasantias",
            "practicante",
            "pasante",
            "internship",
            "becario",
        )
    ):
        return JobType.INTERNSHIP
    if any(k in blob for k in ("temporal", "temporada", "plazo determinado")):
        return JobType.TEMPORARY
    if any(k in blob for k in ("plazo fijo", "contrato a plazo", "contrato fijo")):
        return JobType.CONTRACT
    if any(
        k in blob
        for k in (
            "jornada completa",
            "tiempo completo",
            "full time",
            "tiempo indeterminado",
            "relacion de dependencia",
        )
    ):
        return JobType.FULL_TIME
    if any(k in blob for k in ("contrato", "contract", "obra labor")):
        return JobType.CONTRACT
    return JobType.UNKNOWN


@dataclass(slots=True)
class ParsedSalary:
    """Rango salarial parseado."""

    salary_min: Decimal | None = None
    salary_max: Decimal | None = None
    currency: str | None = None


_SALARY_RANGE_RE = re.compile(
    r"[\$€]?\s*([\d][\d.,]*)\s*(?:[-–a]\s*[\$€]?\s*([\d][\d.,]*))?\s*\(([^)]+)\)",
    re.IGNORECASE,
)


def _parse_amount(value: str) -> Decimal:
    """Convierte montos latinoamericanos (2.000.000,00) a Decimal."""
    cleaned = value.strip()
    if "," in cleaned and "." in cleaned:
        cleaned = cleaned.replace(".", "").replace(",", ".")
    elif "," in cleaned:
        cleaned = cleaned.replace(",", ".")
    return Decimal(cleaned)


def _currency_from_period(period: str, *, country: str = "ar") -> str:
    period_norm = normalize_text(period)
    defaults = {"ar": "ARS", "co": "COP", "mx": "MXN", "pe": "PEN", "cl": "CLP"}
    return defaults.get(country, "USD")


def parse_salary(raw: str | None, *, country: str = "ar") -> ParsedSalary:
    """Parsea salarios de Computrabajo: '$ 2.000.000,00 (Mensual)'."""
    if not raw:
        return ParsedSalary()

    text = raw.strip()
    if "a convenir" in normalize_text(text):
        return ParsedSalary()

    match = _SALARY_RANGE_RE.search(text)
    if not match:
        return ParsedSalary()

    salary_min = _parse_amount(match.group(1))
    salary_max = _parse_amount(match.group(2)) if match.group(2) else None
    currency = _currency_from_period(match.group(3), country=country)

    return ParsedSalary(salary_min=salary_min, salary_max=salary_max, currency=currency)


def clean_description(text: str | None) -> str | None:
    """Limpia ruido de navegación en descripciones de detalle."""
    if not text:
        return None

    cleaned = text.strip()
    markers = (
        "Descripción de la oferta",
        "Oferta\nEmpresa\nEvaluaciones\nOfertas similares",
    )
    for marker in markers:
        if marker in cleaned:
            cleaned = cleaned.split(marker, maxsplit=1)[-1].strip()

    # Quitar líneas-badge del header (contrato, jornada, modalidad)
    badge_words = (
        "a convenir",
        "jornada completa",
        "jornada parcial",
        "contrato por",
        "contrato a plazo",
        "otro tipo de contrato",
        "remoto",
        "presencial",
        "hibrido",
        "híbrido",
    )
    lines = [ln.strip() for ln in cleaned.splitlines() if ln.strip()]
    filtered: list[str] = []
    for line in lines:
        norm = normalize_text(line)
        if line.startswith("$") or any(norm == w or norm.startswith(w) for w in badge_words):
            if len(line) < 100:
                continue
        filtered.append(line)
    cleaned = "\n\n".join(filtered)

    cutoffs = (
        "Ofertas similares",
        "Evaluaciones de",
        "Ver todos los avisos",
        "Empleos en ",
        "90% profesionales recomiendan",
    )
    for cutoff in cutoffs:
        idx = cleaned.find(cutoff)
        if idx > 200:
            cleaned = cleaned[:idx].strip()

    return cleaned or None


def parse_published_at(raw: str | None, *, now: datetime | None = None) -> datetime | None:
    """Parsea ISO 8601 o fechas relativas en español."""
    if not raw:
        return None

    iso_candidate = raw.strip()
    if "T" in iso_candidate:
        try:
            return datetime.fromisoformat(iso_candidate.replace("Z", "+00:00"))
        except ValueError:
            pass

    return parse_posted_at(raw, now=now)


def parse_posted_at(raw: str | None, *, now: datetime | None = None) -> datetime | None:
    """Parsea fechas relativas en español ('hace 2 días', 'hoy', etc.)."""
    if not raw:
        return None

    reference = now or datetime.now(UTC)
    text = normalize_text(raw)

    if "hoy" in text:
        return reference
    if "ayer" in text:
        return reference - timedelta(days=1)

    match = re.search(r"hace\s+(\d+)\s*(hora|horas|dia|dias|semana|semanas|mes|meses)", text)
    if not match:
        return None

    amount = int(match.group(1))
    unit = match.group(2)

    if unit.startswith("hora"):
        return reference - timedelta(hours=amount)
    if unit.startswith("dia"):
        return reference - timedelta(days=amount)
    if unit.startswith("semana"):
        return reference - timedelta(weeks=amount)
    if unit.startswith("mes"):
        return reference - timedelta(days=amount * 30)

    return None
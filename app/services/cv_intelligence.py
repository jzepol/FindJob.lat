"""Lectura y análisis de CV con Gemini (extracción + embedding)."""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field

import structlog
from fastapi import HTTPException, UploadFile, status
from google.genai import types

from app.core.config import settings
from app.models.base import Seniority
from app.models.profile import Profile
from app.services.cv_parser import ALLOWED_EXTENSIONS, MAX_CV_BYTES, _decode_text, _extract_pdf, _normalize
from app.services.embeddings import EmbeddingError, _get_gemini_client, embed_cv_text

logger = structlog.get_logger(__name__)

CV_PARSE_PROMPT = """Sos un asistente de reclutamiento para Latinoamérica. Analizá el CV adjunto.

Extraé la información y respondé ÚNICAMENTE con JSON válido (sin markdown):
{
  "full_name": "nombre completo o null",
  "headline": "titular profesional en una línea o null",
  "skills": ["skill1", "skill2"],
  "seniority": "intern|junior|mid|senior|lead|director|unknown",
  "cv_text": "texto completo del CV, limpio y legible, preservando secciones",
  "summary": "resumen de 1-2 oraciones del perfil del candidato"
}

Reglas:
- skills: máximo 15, técnicas y relevantes para empleo IT/negocios
- seniority: inferí del CV; si no está claro usá "unknown"
- cv_text: incluí experiencia, educación y skills en texto continuo
"""


@dataclass
class CvParseResult:
    cv_text: str
    full_name: str | None = None
    headline: str | None = None
    skills: list[str] = field(default_factory=list)
    seniority: Seniority | None = None
    summary: str | None = None
    parsed_by: str = "gemini"
    embedding_ready: bool = False


def _gemini_model_name() -> str:
    return settings.gemini_model.removeprefix("models/")


def _mime_for_ext(ext: str) -> str:
    return "application/pdf" if ext == ".pdf" else "text/plain"


def _safe_filename(filename: str) -> str:
    """Normaliza nombres con rutas Windows/Linux (solo basename)."""
    cleaned = filename.replace("\\", "/").strip()
    base = os.path.basename(cleaned) or cleaned
    return base[:255]


async def _read_upload(file: UploadFile) -> tuple[bytes, str, str]:
    if not file.filename:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Archivo sin nombre")

    filename = _safe_filename(file.filename)
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="Formato no soportado. Usá PDF o TXT.",
        )

    raw = await file.read()
    if len(raw) > MAX_CV_BYTES:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="El archivo supera 5 MB.")
    if not raw:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Archivo vacío")

    return raw, ext, filename


def _fallback_extract_text(raw: bytes, ext: str) -> str:
    text = _extract_pdf(raw) if ext == ".pdf" else _decode_text(raw)
    return _normalize(text)


def _fallback_parse_metadata(text: str) -> tuple[str | None, str | None, list[str]]:
    """Heurísticas simples cuando Gemini no está disponible."""
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    full_name = lines[0][:200] if lines else None

    headline = None
    for line in lines[1:6]:
        lower = line.lower()
        if any(
            token in lower
            for token in ("desarroll", "ingenier", "analist", "backend", "frontend", "full stack", "especialist")
        ):
            headline = line[:300]
            break

    skills: list[str] = []
    skill_hints = (
        "python",
        "javascript",
        "typescript",
        "react",
        "node",
        "sql",
        "postgresql",
        "docker",
        "aws",
        "git",
        "fastapi",
        "django",
        "java",
        "kotlin",
        "n8n",
        "openai",
        "ia",
        "automatiz",
    )
    lower_text = text.lower()
    for hint in skill_hints:
        if hint in lower_text:
            label = hint.upper() if len(hint) <= 4 else hint.capitalize()
            if label not in skills:
                skills.append(label)
        if len(skills) >= 10:
            break

    return full_name, headline, skills


def _parse_seniority(value: str | None) -> Seniority | None:
    if not value:
        return None
    try:
        return Seniority(value.lower().strip())
    except ValueError:
        return Seniority.UNKNOWN


def _parse_gemini_json(raw: str) -> dict:
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    return json.loads(cleaned)


def _gemini_parse_sync(raw: bytes, ext: str) -> CvParseResult:
    client = _get_gemini_client_sync()
    mime = _mime_for_ext(ext)

    parts: list[types.Part] = [
        types.Part.from_bytes(data=raw, mime_type=mime),
        types.Part.from_text(text=CV_PARSE_PROMPT),
    ]

    response = client.models.generate_content(
        model=_gemini_model_name(),
        contents=[types.Content(role="user", parts=parts)],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.1,
        ),
    )

    text = (response.text or "").strip()
    if not text:
        raise ValueError("Gemini no devolvió contenido")

    data = _parse_gemini_json(text)
    cv_text = _normalize(str(data.get("cv_text") or ""))
    if len(cv_text.strip()) < 50:
        raise ValueError("Texto de CV insuficiente en respuesta de Gemini")

    skills = data.get("skills") or []
    if not isinstance(skills, list):
        skills = []
    skills = [str(s).strip() for s in skills if str(s).strip()][:15]

    return CvParseResult(
        cv_text=cv_text,
        full_name=(data.get("full_name") or None),
        headline=(data.get("headline") or None),
        skills=skills,
        seniority=_parse_seniority(data.get("seniority")),
        summary=(data.get("summary") or None),
        parsed_by="gemini",
    )


def _get_gemini_client_sync():
    """Versión sync para asyncio.to_thread (evita re-entrada en lock async)."""
    import asyncio

    if not settings.gemini_api_key:
        raise EmbeddingError("GEMINI_API_KEY no configurada")

    # Crear cliente directo en el thread worker
    from google import genai

    return genai.Client(api_key=settings.gemini_api_key)


async def parse_cv_file(file: UploadFile) -> CvParseResult:
    """Lee el CV con Gemini; fallback a extracción local si falla la IA."""
    import asyncio

    raw, ext, _ = await _read_upload(file)

    if settings.gemini_api_key:
        try:
            result = await asyncio.to_thread(_gemini_parse_sync, raw, ext)
            logger.info("cv_parsed", provider="gemini", chars=len(result.cv_text))
            return result
        except Exception as exc:
            logger.warning("cv_gemini_parse_failed", error=str(exc))

    text = _fallback_extract_text(raw, ext)
    if len(text.strip()) < 50:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="No se pudo leer el CV. Probá otro archivo.",
        )

    full_name, headline, skills = _fallback_parse_metadata(text)
    return CvParseResult(
        cv_text=text,
        full_name=full_name,
        headline=headline,
        skills=skills,
        parsed_by="fallback",
    )


def _merge_skills(existing: list[str] | None, new: list[str]) -> list[str]:
    merged: list[str] = []
    seen: set[str] = set()
    for skill in (existing or []) + new:
        key = skill.lower()
        if key not in seen:
            seen.add(key)
            merged.append(skill)
    return merged[:20]


async def apply_cv_to_profile(profile: Profile, parsed: CvParseResult) -> CvParseResult:
    """Persiste campos extraídos y genera embedding del CV."""
    profile.cv_text = parsed.cv_text

    if parsed.full_name and not profile.full_name:
        profile.full_name = parsed.full_name[:200]
    if parsed.headline and not profile.headline:
        profile.headline = parsed.headline[:300]
    if parsed.skills:
        profile.skills = _merge_skills(profile.skills, parsed.skills)
    if parsed.seniority and parsed.seniority != Seniority.UNKNOWN and not profile.seniority:
        profile.seniority = parsed.seniority

    if settings.gemini_api_key:
        try:
            profile.cv_embedding = await embed_cv_text(
                parsed.cv_text,
                headline=profile.headline,
                skills=profile.skills,
            )
            parsed.embedding_ready = True
            logger.info("cv_embedded", provider="gemini", dims=len(profile.cv_embedding))
        except EmbeddingError as exc:
            logger.warning("cv_embedding_failed", error=str(exc))

    return parsed


async def process_cv_upload(file: UploadFile, profile: Profile) -> CvParseResult:
    parsed = await parse_cv_file(file)
    return await apply_cv_to_profile(profile, parsed)
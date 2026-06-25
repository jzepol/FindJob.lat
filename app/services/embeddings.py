"""Generación de embeddings vía Gemini API (sin carga local de modelos)."""

from __future__ import annotations

import asyncio
import uuid

import structlog
from google import genai
from google.genai import types
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.offer import Offer

logger = structlog.get_logger(__name__)

_client: genai.Client | None = None
_client_lock = asyncio.Lock()


class EmbeddingError(Exception):
    """Error al generar embeddings con Gemini."""


async def _get_gemini_client() -> genai.Client:
    """Cliente singleton de Gemini."""
    global _client  # noqa: PLW0603
    if _client is not None:
        return _client
    async with _client_lock:
        if _client is None:
            if not settings.gemini_api_key:
                raise EmbeddingError(
                    "GEMINI_API_KEY no configurada. Agregala en .env para generar embeddings."
                )
            _client = genai.Client(api_key=settings.gemini_api_key)
            logger.info(
                "gemini_embedding_client_ready",
                model=settings.gemini_embedding_model,
                dimensions=settings.embedding_dimensions,
            )
    return _client


def build_offer_text(
    *,
    title: str,
    company: str,
    location: str | None = None,
    description: str | None = None,
    max_desc_chars: int | None = None,
) -> str:
    """Texto concatenado para embedear una oferta."""
    limit = max_desc_chars if max_desc_chars is not None else settings.embedding_max_desc_chars
    parts = [title.strip(), company.strip()]
    if location and location.strip():
        parts.append(location.strip())
    if description and description.strip():
        desc = description.strip()
        if len(desc) > limit:
            desc = desc[:limit]
        parts.append(desc)
    return "\n".join(p for p in parts if p)


def offer_to_text(offer: Offer) -> str:
    """Construye el texto de embedding desde un modelo Offer."""
    return build_offer_text(
        title=offer.title,
        company=offer.company,
        location=offer.location,
        description=offer.description,
    )


def _embedding_model_name() -> str:
    """Normaliza nombre del modelo (con o sin prefijo models/)."""
    model = settings.gemini_embedding_model
    return model.removeprefix("models/")


def _embed_batch_sync(
    client: genai.Client,
    texts: list[str],
    *,
    task_type: str | None = None,
) -> list[list[float]]:
    """Llama a embed_content de Gemini (bloqueante)."""
    result = client.models.embed_content(
        model=_embedding_model_name(),
        contents=texts,
        config=types.EmbedContentConfig(
            task_type=task_type or settings.embedding_task_type,
            output_dimensionality=settings.embedding_dimensions,
        ),
    )
    if not result.embeddings:
        raise EmbeddingError("Gemini no devolvió embeddings")

    vectors = [list(emb.values) for emb in result.embeddings]
    if len(vectors) != len(texts):
        raise EmbeddingError(
            f"Gemini devolvió {len(vectors)} embeddings para {len(texts)} textos"
        )
    return vectors


async def encode_texts(
    texts: list[str],
    *,
    task_type: str | None = None,
) -> list[list[float]]:
    """Codifica textos en lotes vía API de Gemini."""
    if not texts:
        return []

    client = await _get_gemini_client()
    batch_size = max(1, settings.embedding_batch_size)
    all_vectors: list[list[float]] = []

    for start in range(0, len(texts), batch_size):
        batch = texts[start : start + batch_size]
        vectors = await asyncio.to_thread(
            _embed_batch_sync, client, batch, task_type=task_type
        )
        all_vectors.extend(vectors)
        if start + batch_size < len(texts) and settings.embedding_request_delay > 0:
            await asyncio.sleep(settings.embedding_request_delay)

    return all_vectors


async def embed_offer_list(session: AsyncSession, offers: list[Offer]) -> int:
    """Genera y persiste embeddings para una lista de ofertas."""
    candidates = [o for o in offers if offer_to_text(o).strip()]
    if not candidates:
        return 0

    texts = [offer_to_text(o) for o in candidates]
    vectors = await encode_texts(texts)

    for offer, vector in zip(candidates, vectors, strict=True):
        if len(vector) != settings.embedding_dimensions:
            raise EmbeddingError(
                f"Dimensión inesperada: {len(vector)} (esperado {settings.embedding_dimensions})"
            )
        offer.embedding = vector

    await session.flush()
    logger.info("offers_embedded", count=len(candidates), provider="gemini")
    return len(candidates)


async def embed_scraped_batch(
    session: AsyncSession,
    *,
    source_id: uuid.UUID,
    external_ids: list[str],
) -> int:
    """Embedea (o re-embedea) todas las ofertas de un batch de scraping."""
    if not external_ids:
        return 0

    result = await session.execute(
        select(Offer).where(
            Offer.source_id == source_id,
            Offer.external_id.in_(external_ids),
        )
    )
    offers = list(result.scalars().all())
    return await embed_offer_list(session, offers)


async def embed_pending_offers(
    session: AsyncSession,
    *,
    source_slug: str | None = None,
    limit: int | None = None,
    force: bool = False,
) -> int:
    """Backfill: ofertas sin embedding (opcionalmente filtradas por fuente)."""
    from app.models.source import Source

    query = select(Offer).order_by(Offer.created_at.asc())
    if not force:
        query = query.where(Offer.embedding.is_(None))
    if source_slug:
        query = query.join(Source).where(Source.slug == source_slug)
    if limit is not None:
        query = query.limit(limit)

    result = await session.execute(query)
    offers = list(result.scalars().all())
    return await embed_offer_list(session, offers)


def build_cv_embedding_text(
    *,
    cv_text: str,
    headline: str | None = None,
    skills: list[str] | None = None,
) -> str:
    """Texto optimizado para embedear el perfil del candidato (query side)."""
    parts: list[str] = []
    if headline and headline.strip():
        parts.append(headline.strip())
    if skills:
        parts.extend(s.strip() for s in skills if s and s.strip())
    body = cv_text.strip()
    limit = settings.embedding_max_desc_chars
    if len(body) > limit:
        body = body[:limit]
    parts.append(body)
    return "\n".join(parts)


async def embed_cv_text(
    cv_text: str,
    *,
    headline: str | None = None,
    skills: list[str] | None = None,
) -> list[float]:
    """Embedding del CV con RETRIEVAL_QUERY para matching con ofertas."""
    text = build_cv_embedding_text(cv_text=cv_text, headline=headline, skills=skills)
    if not text.strip():
        raise EmbeddingError("CV vacío para embedding")

    vectors = await encode_texts([text], task_type=settings.embedding_query_task_type)
    vector = vectors[0]
    if len(vector) != settings.embedding_dimensions:
        raise EmbeddingError(
            f"Dimensión inesperada: {len(vector)} (esperado {settings.embedding_dimensions})"
        )
    return vector
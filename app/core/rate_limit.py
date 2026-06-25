"""Rate limiting en memoria (por IP)."""

from __future__ import annotations

import time
from collections import defaultdict

from fastapi import HTTPException, Request, status

_buckets: dict[str, list[float]] = defaultdict(list)


def client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


def check_rate_limit(
    request: Request,
    *,
    scope: str,
    max_requests: int = 5,
    window_seconds: int = 60,
) -> None:
    key = f"{scope}:{client_ip(request)}"
    now = time.time()
    hits = [t for t in _buckets[key] if now - t < window_seconds]
    if len(hits) >= max_requests:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Demasiados intentos. Esperá un minuto e intentá de nuevo.",
        )
    hits.append(now)
    _buckets[key] = hits
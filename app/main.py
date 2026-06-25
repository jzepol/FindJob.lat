"""Aplicación FastAPI — API REST para Findjob.lat."""

from __future__ import annotations

import os

from dotenv import load_dotenv

# Antes de cualquier import OAuth: permitir http://localhost en desarrollo
load_dotenv()
if os.getenv("APP_ENV", "development") == "development":
    os.environ.setdefault("OAUTHLIB_INSECURE_TRANSPORT", "1")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import auth, company_reports, meta, offers, users
from app.core.config import settings
from app.middleware.security_headers import SecurityHeadersMiddleware

_docs = "/docs" if settings.is_development else None
_openapi = "/openapi.json" if settings.is_development else None

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="API de búsqueda y matching de ofertas laborales LATAM",
    docs_url=_docs,
    redoc_url="/redoc" if settings.is_development else None,
    openapi_url=_openapi,
)

_cors_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://findjob.lat",
    "https://www.findjob.lat",
]

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(company_reports.router, prefix="/api/v1")
app.include_router(offers.router, prefix="/api/v1")
app.include_router(meta.router, prefix="/api/v1")


@app.get("/api/v1/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
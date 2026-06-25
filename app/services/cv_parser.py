"""Extracción de texto desde archivos de CV."""

from __future__ import annotations

import io

from fastapi import HTTPException, UploadFile, status
from pypdf import PdfReader

MAX_CV_BYTES = 5 * 1024 * 1024
MAX_CV_CHARS = 50_000
ALLOWED_EXTENSIONS = {".pdf", ".txt"}


async def extract_cv_text(file: UploadFile) -> str:
    """Lee un PDF o TXT y devuelve texto plano normalizado."""
    if not file.filename:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Archivo sin nombre")

    ext = "." + file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="Formato no soportado. Usá PDF o TXT.",
        )

    raw = await file.read()
    if len(raw) > MAX_CV_BYTES:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="El archivo supera el límite de 5 MB.",
        )
    if not raw:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Archivo vacío")

    if ext == ".txt":
        text = _decode_text(raw)
    else:
        text = _extract_pdf(raw)

    text = _normalize(text)
    if len(text.strip()) < 50:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="No se pudo extraer suficiente texto del CV. Probá otro archivo o pegá el texto manualmente.",
        )

    return text[:MAX_CV_CHARS]


def _decode_text(raw: bytes) -> str:
    for encoding in ("utf-8", "latin-1", "cp1252"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="No se pudo leer el archivo de texto")


def _extract_pdf(raw: bytes) -> str:
    try:
        reader = PdfReader(io.BytesIO(raw))
    except Exception as exc:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="PDF inválido o protegido con contraseña",
        ) from exc

    parts: list[str] = []
    for page in reader.pages:
        extracted = page.extract_text()
        if extracted:
            parts.append(extracted)

    return "\n".join(parts)


def _normalize(text: str) -> str:
    lines = [line.strip() for line in text.replace("\r\n", "\n").split("\n")]
    collapsed: list[str] = []
    for line in lines:
        if not line and collapsed and collapsed[-1] == "":
            continue
        collapsed.append(line)
    return "\n".join(collapsed).strip()
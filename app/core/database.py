"""Conexión async a PostgreSQL con soporte pgvector."""

from collections.abc import AsyncGenerator

from pgvector.sqlalchemy import Vector
from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

# Convención de nombres para constraints (útil en migraciones Alembic)
NAMING_CONVENTION: dict[str, str] = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

metadata = MetaData(naming_convention=NAMING_CONVENTION)


class Base(DeclarativeBase):
    """Base declarativa SQLAlchemy 2.0."""

    metadata = metadata


# Dimensión fija de embeddings (Gemini gemini-embedding-001, output_dimensionality)
EMBEDDING_DIM = settings.embedding_dimensions


def embedding_column(nullable: bool = True) -> Vector:
    """Factory para columnas Vector(384) reutilizables."""
    return Vector(EMBEDDING_DIM)  # type: ignore[return-value]


engine: AsyncEngine = create_async_engine(
    settings.database_url_str,
    echo=settings.database_echo,
    pool_size=settings.database_pool_size,
    max_overflow=settings.database_max_overflow,
    pool_pre_ping=True,
)

async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency injection para FastAPI — yield de sesión async."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_db() -> None:
    """Crea extensiones necesarias (pgvector). Usar solo en dev/tests."""
    async with engine.begin() as conn:
        await conn.exec_driver_sql("CREATE EXTENSION IF NOT EXISTS vector")


async def close_db() -> None:
    """Cierra el pool de conexiones al apagar la app."""
    await engine.dispose()
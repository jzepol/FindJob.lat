"""Embeddings Gemini 768d (antes 384d local).

Revision ID: a1b2c3d4e5f6
Revises: 27db3a4305d2
Create Date: 2026-06-16

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: str | None = "27db3a4305d2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Vectores 384d incompatibles con Gemini → limpiar antes de cambiar dimensión
    op.execute("UPDATE offers SET embedding = NULL WHERE embedding IS NOT NULL")
    op.execute("UPDATE profiles SET cv_embedding = NULL WHERE cv_embedding IS NOT NULL")

    op.alter_column(
        "offers",
        "embedding",
        existing_type=Vector(384),
        type_=Vector(768),
        existing_nullable=True,
    )
    op.alter_column(
        "profiles",
        "cv_embedding",
        existing_type=Vector(384),
        type_=Vector(768),
        existing_nullable=True,
        existing_comment="Embedding del CV para matching semántico",
    )


def downgrade() -> None:
    op.execute("UPDATE offers SET embedding = NULL WHERE embedding IS NOT NULL")
    op.execute("UPDATE profiles SET cv_embedding = NULL WHERE cv_embedding IS NOT NULL")

    op.alter_column(
        "profiles",
        "cv_embedding",
        existing_type=Vector(768),
        type_=Vector(384),
        existing_nullable=True,
        existing_comment="Embedding del CV para matching semántico",
    )
    op.alter_column(
        "offers",
        "embedding",
        existing_type=Vector(768),
        type_=Vector(384),
        existing_nullable=True,
    )
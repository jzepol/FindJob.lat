"""Auth OAuth, karma y reportes de empresas.

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-06-17

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "b2c3d4e5f6a7"
down_revision: str | None = "a1b2c3d4e5f6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("karma_score", sa.Integer(), server_default="0", nullable=False))

    op.alter_column("users", "hashed_password", existing_type=sa.String(255), nullable=True)

    op.create_table(
        "oauth_accounts",
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("provider", sa.Enum("google", "linkedin", name="oauthprovider"), nullable=False),
        sa.Column("provider_user_id", sa.String(255), nullable=False),
        sa.Column("email", sa.String(320), nullable=True),
        sa.Column("display_name", sa.String(200), nullable=True),
        sa.Column("avatar_url", sa.String(1024), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("provider", "provider_user_id", name="uq_oauth_provider_subject"),
    )
    op.create_index("ix_oauth_accounts_user_id", "oauth_accounts", ["user_id"])

    op.create_table(
        "karma_events",
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column(
            "event_type",
            sa.Enum(
                "oauth_linked",
                "profile_complete",
                "cv_uploaded",
                "first_search",
                "email_verified",
                name="karmaeventtype",
            ),
            nullable=False,
        ),
        sa.Column("points", sa.Integer(), nullable=False),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "event_type", name="uq_karma_user_event"),
    )
    op.create_index("ix_karma_events_user_id", "karma_events", ["user_id"])

    op.create_table(
        "company_reports",
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("offer_id", sa.UUID(), nullable=True),
        sa.Column("company_name", sa.String(255), nullable=False),
        sa.Column("normalized_company", sa.String(255), nullable=False),
        sa.Column(
            "report_type",
            sa.Enum(
                "ghost_job",
                "high_turnover",
                "misleading_salary",
                "ats_black_hole",
                "other",
                name="companyreporttype",
            ),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum("pending", "verified", "rejected", name="companyreportstatus"),
            server_default="pending",
            nullable=False,
        ),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["offer_id"], ["offers.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_company_reports_company", "company_reports", ["normalized_company"])
    op.create_index("ix_company_reports_status", "company_reports", ["status"])
    op.create_index("ix_company_reports_user_company", "company_reports", ["user_id", "normalized_company"])
    op.create_index("ix_company_reports_offer_id", "company_reports", ["offer_id"])
    op.create_index("ix_company_reports_normalized_company", "company_reports", ["normalized_company"])


def downgrade() -> None:
    op.drop_index("ix_company_reports_normalized_company", "company_reports")
    op.drop_index("ix_company_reports_offer_id", "company_reports")
    op.drop_index("ix_company_reports_user_company", "company_reports")
    op.drop_index("ix_company_reports_status", "company_reports")
    op.drop_index("ix_company_reports_company", "company_reports")
    op.drop_table("company_reports")
    op.drop_index("ix_karma_events_user_id", "karma_events")
    op.drop_table("karma_events")
    op.drop_index("ix_oauth_accounts_user_id", "oauth_accounts")
    op.drop_table("oauth_accounts")
    op.drop_column("users", "karma_score")
    op.alter_column("users", "hashed_password", existing_type=sa.String(255), nullable=False)
    op.execute("DROP TYPE IF EXISTS companyreportstatus")
    op.execute("DROP TYPE IF EXISTS companyreporttype")
    op.execute("DROP TYPE IF EXISTS karmaeventtype")
    op.execute("DROP TYPE IF EXISTS oauthprovider")
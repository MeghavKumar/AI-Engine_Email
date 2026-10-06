"""minimize research audit event data

Revision ID: d5dae9dedada
Revises: 149c348078a1
Create Date: 2026-10-06 03:22:22.410648

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "d5dae9dedada"
down_revision: Union[str, Sequence[str], None] = "149c348078a1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Minimize research audit event data."""
    op.drop_column("research_audit_events", "evidence_hash")
    op.drop_column("research_audit_events", "candidate_email")
    op.drop_column("research_audit_events", "candidate_name")
    op.drop_column("research_audit_events", "metadata")

    op.add_column(
        "research_audit_events",
        sa.Column("verification_status", sa.String(length=50), nullable=True),
    )
    op.add_column(
        "research_audit_events",
        sa.Column("candidate_count", sa.Integer(), nullable=True),
    )
    op.add_column(
        "research_audit_events",
        sa.Column("decision", sa.String(length=50), nullable=True),
    )

    op.create_index(
        op.f("ix_research_audit_events_verification_status"),
        "research_audit_events",
        ["verification_status"],
        unique=False,
    )


def downgrade() -> None:
    """Restore the previous research audit event schema."""
    op.drop_index(
        op.f("ix_research_audit_events_verification_status"),
        table_name="research_audit_events",
    )

    op.drop_column("research_audit_events", "decision")
    op.drop_column("research_audit_events", "candidate_count")
    op.drop_column("research_audit_events", "verification_status")

    op.add_column(
        "research_audit_events",
        sa.Column(
            "metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'"),
        ),
    )
    op.add_column(
        "research_audit_events",
        sa.Column("candidate_name", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "research_audit_events",
        sa.Column("candidate_email", sa.String(length=320), nullable=True),
    )
    op.add_column(
        "research_audit_events",
        sa.Column("evidence_hash", sa.String(length=64), nullable=True),
    )

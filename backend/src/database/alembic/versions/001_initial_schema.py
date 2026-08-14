"""initial schema

Revision ID: 001_initial_schema
Revises:
Create Date: 2026-08-14 10:30:00.000000

"""

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001_initial_schema"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Create tickets table
    op.create_table(
        "tickets",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("external_client_id", sa.String(length=255), nullable=False),
        sa.Column("topic", sa.String(length=255), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column(
            "status",
            sa.Enum("open", "closed", name="ticket_status"),
            nullable=False,
            server_default="open",
        ),
        sa.Column(
            "sla_status",
            sa.Enum("normal", "warning", "overdue", name="sla_status"),
            nullable=False,
            server_default="normal",
        ),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("first_response_time", sa.Interval(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_tickets_id"), "tickets", ["id"], unique=False)
    op.create_index(
        op.f("ix_tickets_external_client_id"), "tickets", ["external_client_id"], unique=False
    )
    op.create_index(op.f("ix_tickets_topic"), "tickets", ["topic"], unique=False)
    op.create_index(op.f("ix_tickets_status"), "tickets", ["status"], unique=False)
    op.create_index(op.f("ix_tickets_sla_status"), "tickets", ["sla_status"], unique=False)
    op.create_index(op.f("ix_tickets_created_at"), "tickets", ["created_at"], unique=False)
    op.create_index("ix_tickets_status_topic", "tickets", ["status", "topic"], unique=False)
    op.create_index(
        "ix_tickets_status_created_at", "tickets", ["status", "created_at"], unique=False
    )

    # 2. Create events table
    op.create_table(
        "events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("external_event_id", sa.String(length=255), nullable=False),
        sa.Column(
            "event_type",
            sa.Enum("client", "agent", name="event_type"),
            nullable=False,
        ),
        sa.Column("ticket_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["ticket_id"], ["tickets.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("external_event_id"),
    )
    op.create_index(op.f("ix_events_id"), "events", ["id"], unique=False)
    op.create_index(
        op.f("ix_events_external_event_id"), "events", ["external_event_id"], unique=True
    )
    op.create_index(op.f("ix_events_ticket_id"), "events", ["ticket_id"], unique=False)

    # 3. Create outbox_events table
    op.create_table(
        "outbox_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("ticket_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "status",
            sa.Enum("pending", "processing", "done", "failed", name="outbox_status"),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("available_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["ticket_id"], ["tickets.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_outbox_events_id"), "outbox_events", ["id"], unique=False)
    op.create_index(
        op.f("ix_outbox_events_ticket_id"), "outbox_events", ["ticket_id"], unique=False
    )
    op.create_index(
        op.f("ix_outbox_events_event_type"), "outbox_events", ["event_type"], unique=False
    )
    op.create_index(op.f("ix_outbox_events_status"), "outbox_events", ["status"], unique=False)
    op.create_index(
        op.f("ix_outbox_events_available_at"), "outbox_events", ["available_at"], unique=False
    )
    op.create_index(
        "ix_outbox_status_available_at", "outbox_events", ["status", "available_at"], unique=False
    )


def downgrade() -> None:
    op.drop_table("outbox_events")
    op.execute("DROP TYPE IF EXISTS outbox_status")
    op.drop_table("events")
    op.execute("DROP TYPE IF EXISTS event_type")
    op.drop_table("tickets")
    op.execute("DROP TYPE IF EXISTS ticket_status")
    op.execute("DROP TYPE IF EXISTS sla_status")

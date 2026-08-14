import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from src.routers.events.models import EventType


class EventIngestRequest(BaseModel):
    external_event_id: str = Field(
        ...,
        description="Unique stable event identifier for idempotency",
        examples=["evt_client_101", "evt_agent_202"],
    )
    event_type: EventType = Field(
        ...,
        description="Type of the event: client (new ticket) or agent (response)",
        examples=["client", "agent"],
    )
    received_at: datetime | None = Field(
        default=None,
        description="Timestamp when event occurred (defaults to current time)",
    )
    # Fields for client events
    external_client_id: str | None = Field(
        default=None,
        description="Identifier of client or communication channel",
        examples=["client_tg_450", "crm_user_891"],
    )
    topic: str | None = Field(
        default=None,
        description="Support topic / department",
        examples=["Billing", "Technical Support", "General"],
    )
    content: str | None = Field(
        default=None,
        description="Message content / text",
        examples=["Cannot complete payment", "I have reviewed your request, problem solved."],
    )
    # Field for agent events
    ticket_id: uuid.UUID | None = Field(
        default=None,
        description="ID of the ticket being answered (required for agent event if known)",
    )
    payload: dict[str, Any] | None = Field(
        default=None,
        description="Optional additional event metadata",
    )


class EventIngestResponse(BaseModel):
    status: str = Field(..., examples=["created", "duplicate", "processed"])
    external_event_id: str
    ticket_id: uuid.UUID | None = None
    event_type: EventType
    message: str

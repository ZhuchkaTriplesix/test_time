import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from src.routers.tickets.models import SLAStatus, TicketStatus


class TicketResponse(BaseModel):
    id: uuid.UUID
    external_client_id: str
    topic: str
    content: str
    status: TicketStatus
    sla_status: SLAStatus
    created_at: datetime
    closed_at: datetime | None = None
    wait_time_seconds: float = Field(
        ...,
        description="Elapsed wait time in seconds (calculated dynamically from creation)",
    )
    first_response_time_seconds: float | None = Field(
        default=None,
        description="First response time in seconds for closed tickets",
    )


class TicketListResponse(BaseModel):
    tickets: list[TicketResponse]
    total: int
    available_topics: list[str]

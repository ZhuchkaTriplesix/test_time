from datetime import datetime

from pydantic import BaseModel, Field


class MetricsResponse(BaseModel):
    total_created: int = Field(..., description="Total number of tickets created in the system")
    total_answered: int = Field(..., description="Total number of tickets answered (closed)")
    total_overdue: int = Field(..., description="Total number of tickets marked as overdue")
    median_first_response_time_seconds: float | None = Field(
        default=None,
        description="Median first response time in seconds (calculated via PostgreSQL percentile_cont)",
    )
    period_from: datetime | None = None
    period_to: datetime | None = None

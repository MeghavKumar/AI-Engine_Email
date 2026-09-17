from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class ScheduledJobType(str, Enum):
    FOLLOW_UP_CHECK = "FOLLOW_UP_CHECK"
    REMINDER = "REMINDER"


class ScheduledJobStatus(str, Enum):
    SCHEDULED = "SCHEDULED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class ScheduledJob(BaseModel):
    id: str
    user_id: str
    job_type: ScheduledJobType
    email_thread_id: str
    scheduled_for: datetime
    status: ScheduledJobStatus = ScheduledJobStatus.SCHEDULED
    attempts: int = Field(default=0, ge=0)
    payload: dict = Field(default_factory=dict)
    created_at: datetime
    completed_at: datetime | None = None

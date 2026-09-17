from enum import Enum

from pydantic import BaseModel


class FollowUpOutcome(str, Enum):
    REPLY_RECEIVED = "REPLY_RECEIVED"
    NO_REPLY = "NO_REPLY"


class FollowUpExecutionResult(BaseModel):
    job_id: str
    outcome: FollowUpOutcome
    reply_message_id: str | None = None
    notification_required: bool = False
    notification_reason: str | None = None

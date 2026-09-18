from enum import Enum

from pydantic import BaseModel


class NotificationType(str, Enum):
    NO_REPLY = "NO_REPLY"


class NotificationStatus(str, Enum):
    PENDING = "PENDING"
    SENT = "SENT"
    FAILED = "FAILED"


class Notification(BaseModel):
    notification_id: str
    notification_type: NotificationType
    status: NotificationStatus = NotificationStatus.PENDING
    user_id: str
    subject: str
    message: str

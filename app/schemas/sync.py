from typing import Literal

from pydantic import BaseModel, Field


class SyncPage(BaseModel):
    """A provider-independent page of mailbox messages."""

    messages: list[dict] = Field(default_factory=list)
    next_cursor: str | None = None


class SyncChange(BaseModel):
    """A provider-independent mailbox change."""

    change_type: Literal["upsert", "delete"]
    message_id: str
    message: dict | None = None


class SyncChanges(BaseModel):
    """A provider-independent batch of incremental mailbox changes."""

    changes: list[SyncChange] = Field(default_factory=list)
    next_cursor: str | None = None
    checkpoint_cursor: str | None = None
    has_more: bool = False

from pathlib import Path

from pydantic import BaseModel, Field


class EmailAttachment(BaseModel):
    """A verified file that is ready to be attached to an email."""

    filename: str = Field(min_length=1)
    content_type: str = Field(min_length=1)
    file_path: Path

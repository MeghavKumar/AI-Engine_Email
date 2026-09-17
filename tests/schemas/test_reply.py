import pytest
from pydantic import ValidationError

from app.schemas.reply import ReplyDetectionResult


def test_reply_detection_result_with_reply():
    result = ReplyDetectionResult(
        replied=True,
        reply_message_id="reply-123",
        reply_from="person@example.com",
    )

    assert result.replied is True
    assert result.reply_message_id == "reply-123"
    assert result.reply_from == "person@example.com"


def test_reply_detection_result_without_reply():
    result = ReplyDetectionResult(
        replied=False,
    )

    assert result.replied is False
    assert result.reply_message_id is None
    assert result.reply_from is None


def test_reply_detection_result_rejects_invalid_email():
    with pytest.raises(ValidationError):
        ReplyDetectionResult(
            replied=True,
            reply_message_id="reply-123",
            reply_from="not-an-email",
        )

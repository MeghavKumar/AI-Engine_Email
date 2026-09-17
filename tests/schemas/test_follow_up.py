from app.schemas.follow_up import (
    FollowUpExecutionResult,
    FollowUpOutcome,
)


def test_follow_up_result_for_reply():
    result = FollowUpExecutionResult(
        job_id="job-123",
        outcome=FollowUpOutcome.REPLY_RECEIVED,
        reply_message_id="reply-456",
    )

    assert result.outcome == FollowUpOutcome.REPLY_RECEIVED
    assert result.reply_message_id == "reply-456"
    assert result.notification_required is False


def test_follow_up_result_for_no_reply():
    result = FollowUpExecutionResult(
        job_id="job-456",
        outcome=FollowUpOutcome.NO_REPLY,
        notification_required=True,
        notification_reason="No reply received after follow-up period.",
    )

    assert result.outcome == FollowUpOutcome.NO_REPLY
    assert result.reply_message_id is None
    assert result.notification_required is True
    assert result.notification_reason == (
        "No reply received after follow-up period."
    )

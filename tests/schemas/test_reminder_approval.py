from app.schemas.reminder import (
    ReminderApprovalDecision,
    ReminderApprovalRequest,
    ReminderApprovalStatus,
)


def test_reminder_approval_request_defaults_to_pending():
    request = ReminderApprovalRequest(
        request_id="reminder-123",
        requested_by="user-123",
        reason="Reminder requires human approval before sending.",
    )

    assert request.status == ReminderApprovalStatus.PENDING


def test_reminder_approval_request_accepts_explicit_status():
    request = ReminderApprovalRequest(
        request_id="reminder-123",
        status=ReminderApprovalStatus.APPROVED,
        requested_by="user-123",
        reason="Reminder approved for sending.",
    )

    assert request.status == ReminderApprovalStatus.APPROVED


def test_reminder_approval_decision():
    decision = ReminderApprovalDecision(
        request_id="reminder-123",
        status=ReminderApprovalStatus.APPROVED,
        decided_by="user-123",
        comment="Recipients and content verified.",
    )

    assert decision.request_id == "reminder-123"
    assert decision.status == ReminderApprovalStatus.APPROVED
    assert decision.decided_by == "user-123"
    assert decision.comment == "Recipients and content verified."


def test_reminder_approval_decision_can_be_rejected():
    decision = ReminderApprovalDecision(
        request_id="reminder-123",
        status=ReminderApprovalStatus.REJECTED,
        decided_by="user-123",
    )

    assert decision.status == ReminderApprovalStatus.REJECTED
    assert decision.comment is None

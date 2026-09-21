import pytest

from app.schemas.reminder import (
    ReminderApprovalDecision,
    ReminderApprovalStatus,
    ReminderDraft,
    ReminderStatus,
)
from app.services.reminder_approval import ReminderApprovalService


def make_reminder() -> ReminderDraft:
    return ReminderDraft(
        to=["recipient@example.com"],
        subject="Follow-up",
        body="Just following up on my previous email.",
    )


def test_create_request():
    service = ReminderApprovalService()
    reminder = make_reminder()

    request = service.create_request(
        reminder=reminder,
        requested_by="user-123",
        reason="Reminder requires human approval before sending.",
    )

    assert request.request_id
    assert request.status == ReminderApprovalStatus.PENDING
    assert request.requested_by == "user-123"


def test_approved_decision_approves_reminder():
    service = ReminderApprovalService()
    reminder = make_reminder()

    request = service.create_request(
        reminder=reminder,
        requested_by="user-123",
        reason="Review reminder before sending.",
    )

    decision = ReminderApprovalDecision(
        request_id=request.request_id,
        status=ReminderApprovalStatus.APPROVED,
        decided_by="user-123",
        comment="Approved.",
    )

    result = service.apply_decision(
        reminder=reminder,
        request=request,
        decision=decision,
    )

    assert result.status == ReminderStatus.APPROVED


def test_rejected_decision_rejects_reminder():
    service = ReminderApprovalService()
    reminder = make_reminder()

    request = service.create_request(
        reminder=reminder,
        requested_by="user-123",
        reason="Review reminder before sending.",
    )

    decision = ReminderApprovalDecision(
        request_id=request.request_id,
        status=ReminderApprovalStatus.REJECTED,
        decided_by="user-123",
        comment="Please revise.",
    )

    result = service.apply_decision(
        reminder=reminder,
        request=request,
        decision=decision,
    )

    assert result.status == ReminderStatus.REJECTED


def test_mismatched_request_id_is_rejected():
    service = ReminderApprovalService()
    reminder = make_reminder()

    request = service.create_request(
        reminder=reminder,
        requested_by="user-123",
        reason="Review reminder before sending.",
    )

    decision = ReminderApprovalDecision(
        request_id="different-request",
        status=ReminderApprovalStatus.APPROVED,
        decided_by="user-123",
    )

    with pytest.raises(ValueError, match="does not match"):
        service.apply_decision(
            reminder=reminder,
            request=request,
            decision=decision,
        )


def test_non_pending_request_cannot_be_decided_again():
    service = ReminderApprovalService()
    reminder = make_reminder()

    request = service.create_request(
        reminder=reminder,
        requested_by="user-123",
        reason="Review reminder before sending.",
    )

    request.status = ReminderApprovalStatus.APPROVED

    decision = ReminderApprovalDecision(
        request_id=request.request_id,
        status=ReminderApprovalStatus.REJECTED,
        decided_by="user-123",
    )

    with pytest.raises(ValueError, match="already been decided"):
        service.apply_decision(
            reminder=reminder,
            request=request,
            decision=decision,
        )


def test_non_draft_reminder_cannot_enter_approval():
    service = ReminderApprovalService()
    reminder = make_reminder()
    reminder.status = ReminderStatus.APPROVED

    with pytest.raises(ValueError, match="Only draft reminders"):
        service.create_request(
            reminder=reminder,
            requested_by="user-123",
            reason="Review reminder before sending.",
        )

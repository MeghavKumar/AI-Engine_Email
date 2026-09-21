import pytest
from pydantic import ValidationError

from app.schemas.reminder import ReminderDraft, ReminderStatus


def test_create_reminder_draft():
    reminder = ReminderDraft(
        to=["recipient@example.com"],
        subject="Following up",
        body="Just following up on my previous email.",
    )

    assert reminder.to == ["recipient@example.com"]
    assert reminder.subject == "Following up"
    assert reminder.body == "Just following up on my previous email."
    assert reminder.status == ReminderStatus.DRAFT


def test_reminder_requires_recipient():
    with pytest.raises(ValidationError):
        ReminderDraft(
            to=[],
            subject="Following up",
            body="Just following up.",
        )


def test_reminder_requires_subject():
    with pytest.raises(ValidationError):
        ReminderDraft(
            to=["recipient@example.com"],
            subject="",
            body="Just following up.",
        )


def test_reminder_requires_body():
    with pytest.raises(ValidationError):
        ReminderDraft(
            to=["recipient@example.com"],
            subject="Following up",
            body="",
        )


def test_reminder_status_can_be_updated():
    reminder = ReminderDraft(
        to=["recipient@example.com"],
        subject="Following up",
        body="Just following up.",
    )

    reminder.status = ReminderStatus.APPROVED

    assert reminder.status == ReminderStatus.APPROVED


def test_reminder_defaults_to_no_attachment_required():
    reminder = ReminderDraft(
        to=["recipient@example.com"],
        subject="Following up",
        body="Just following up.",
    )

    assert reminder.attachment_required is False
    assert reminder.attachment_names == []


def test_reminder_can_require_attachments():
    reminder = ReminderDraft(
        to=["recipient@example.com"],
        subject="Following up",
        body="Please see the attached document.",
        attachment_required=True,
        attachment_names=["document.pdf"],
    )

    assert reminder.attachment_required is True
    assert reminder.attachment_names == ["document.pdf"]

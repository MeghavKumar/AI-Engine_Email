from pathlib import Path

import pytest

from app.schemas.attachment import (
    AttachmentVerificationResult,
    AttachmentVerificationStatus,
)
from app.schemas.email_attachment import EmailAttachment
from app.schemas.reminder import ReminderDraft, ReminderStatus
from app.services.reminder_send import ReminderSendService


class FakeEmailProvider:
    def __init__(self):
        self.sent_messages = []

    def send_message(
        self,
        account_id: str,
        message: dict,
    ) -> str:
        self.sent_messages.append(
            {
                "account_id": account_id,
                "message": message,
            }
        )
        return "provider-message-123"


def make_reminder(status: ReminderStatus) -> ReminderDraft:
    return ReminderDraft(
        to=["recipient@example.com"],
        cc=["copy@example.com"],
        subject="Follow-up",
        body="Just following up on my previous email.",
        status=status,
    )


def test_approved_reminder_is_sent():
    provider = FakeEmailProvider()
    service = ReminderSendService(provider)

    reminder = make_reminder(ReminderStatus.APPROVED)

    message_id = service.send(
        reminder=reminder,
        account_id="account-123",
    )

    assert message_id == "provider-message-123"
    assert len(provider.sent_messages) == 1

    sent = provider.sent_messages[0]

    assert sent["account_id"] == "account-123"
    assert sent["message"]["to"] == ["recipient@example.com"]
    assert sent["message"]["cc"] == ["copy@example.com"]
    assert sent["message"]["subject"] == "Follow-up"
    assert sent["message"]["body"] == (
        "Just following up on my previous email."
    )


def test_draft_reminder_cannot_be_sent():
    provider = FakeEmailProvider()
    service = ReminderSendService(provider)

    reminder = make_reminder(ReminderStatus.DRAFT)

    with pytest.raises(
        ValueError,
        match="not approved for sending",
    ):
        service.send(
            reminder=reminder,
            account_id="account-123",
        )

    assert provider.sent_messages == []


def test_rejected_reminder_cannot_be_sent():
    provider = FakeEmailProvider()
    service = ReminderSendService(provider)

    reminder = make_reminder(ReminderStatus.REJECTED)

    with pytest.raises(
        ValueError,
        match="not approved for sending",
    ):
        service.send(
            reminder=reminder,
            account_id="account-123",
        )

    assert provider.sent_messages == []


def test_required_attachment_without_verification_cannot_be_sent():
    provider = FakeEmailProvider()
    service = ReminderSendService(provider)

    reminder = ReminderDraft(
        to=["recipient@example.com"],
        subject="Follow-up",
        body="Please see the attached document.",
        attachment_required=True,
        attachment_names=["document.pdf"],
        status=ReminderStatus.APPROVED,
    )

    with pytest.raises(
        ValueError,
        match="Attachment verification is required",
    ):
        service.send(
            reminder=reminder,
            account_id="account-123",
        )

    assert provider.sent_messages == []


def test_required_attachment_missing_cannot_be_sent():
    provider = FakeEmailProvider()
    service = ReminderSendService(provider)

    reminder = ReminderDraft(
        to=["recipient@example.com"],
        subject="Follow-up",
        body="Please see the attached document.",
        attachment_required=True,
        attachment_names=["document.pdf"],
        status=ReminderStatus.APPROVED,
    )

    verification = AttachmentVerificationResult(
        status=AttachmentVerificationStatus.MISSING,
        required=True,
        attachment_names=["document.pdf"],
        missing_attachments=["document.pdf"],
        reason="Required attachment is missing.",
    )

    with pytest.raises(
        ValueError,
        match="not verified for sending",
    ):
        service.send(
            reminder=reminder,
            account_id="account-123",
            attachment_verification=verification,
        )

    assert provider.sent_messages == []


def test_verified_required_attachment_allows_reminder_to_be_sent():
    provider = FakeEmailProvider()
    service = ReminderSendService(provider)

    reminder = ReminderDraft(
        to=["recipient@example.com"],
        subject="Follow-up",
        body="Please see the attached document.",
        attachment_required=True,
        attachment_names=["document.pdf"],
        status=ReminderStatus.APPROVED,
    )

    verification = AttachmentVerificationResult(
        status=AttachmentVerificationStatus.VERIFIED,
        required=True,
        attachment_names=["document.pdf"],
        reason="All required attachments are present.",
    )

    attachment = EmailAttachment(
        filename="document.pdf",
        content_type="application/pdf",
        file_path=Path("/tmp/document.pdf"),
    )

    message_id = service.send(
        reminder=reminder,
        account_id="account-123",
        attachment_verification=verification,
        attachments=[attachment],
    )

    assert message_id == "provider-message-123"
    assert len(provider.sent_messages) == 1

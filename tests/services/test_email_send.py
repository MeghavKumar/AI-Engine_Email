import pytest

from app.providers.email.base import EmailProvider
from app.schemas.attachment import (
    AttachmentVerificationResult,
    AttachmentVerificationStatus,
)
from app.schemas.email import (
    ApprovalStatus,
    EmailDraft,
    SecurityAssessment,
)
from app.schemas.recipient import (
    RecipientCandidate,
    RecipientVerificationDecision,
    RecipientVerificationStatus,
)
from app.schemas.workflow import (
    EmailWorkflowState,
    EmailWorkflowStatus,
)
from app.services.email_send import EmailSendService
from app.services.draft_integrity import draft_fingerprint


class FakeEmailProvider(EmailProvider):
    """Fake provider used to test sending without real email."""

    def __init__(self):
        self.sent_messages = []

    def list_messages(
        self,
        account_id: str,
        max_results: int = 25,
    ) -> list[dict]:
        return []

    def get_message(
        self,
        account_id: str,
        message_id: str,
    ) -> dict:
        raise NotImplementedError

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
        return "fake-message-001"

    def mark_read(
        self,
        account_id: str,
        message_id: str,
    ) -> None:
        raise NotImplementedError

    def archive_message(
        self,
        account_id: str,
        message_id: str,
    ) -> None:
        raise NotImplementedError

    def get_thread(
        self,
        account_id: str,
        thread_id: str,
    ) -> list[dict]:
        raise NotImplementedError


def make_approved_state() -> EmailWorkflowState:
    draft = EmailDraft(
        to=["ai-generated@example.com"],
        subject="Project update",
        body="Here is the project update.",
        confidence=0.95,
    )

    approved_recipient = RecipientCandidate(
        name="Approved Recipient",
        email="approved@example.com",
        source="human_verified",
        confidence=1.0,
        reason="Approved by the user.",
    )

    recipient_decision = RecipientVerificationDecision(
        request_id="recipient-001",
        status=RecipientVerificationStatus.APPROVED,
        decided_by="user-001",
        approved_recipients=[approved_recipient],
    )

    attachment_result = AttachmentVerificationResult(
        status=AttachmentVerificationStatus.NOT_REQUIRED,
        required=False,
        reason="No attachment is required.",
    )

    security_assessment = SecurityAssessment(
        safe=True,
        pii_detected=False,
        prompt_injection_detected=False,
        reasons=[],
    )

    state = EmailWorkflowState(
        workflow_id="workflow-001",
        status=EmailWorkflowStatus.READY_TO_SEND,
        draft=draft,
        recipient_verification_decision=recipient_decision,
        attachment_verification_result=attachment_result,
        security_assessment=security_assessment,
        send_approval_decision={
            "request_id": "send-001",
            "status": ApprovalStatus.APPROVED,
            "decided_by": "user-001",
        },
    )
    state.approved_draft_fingerprint = draft_fingerprint(state)
    return state


def test_approved_workflow_sends_message():
    provider = FakeEmailProvider()
    service = EmailSendService(provider)

    state = make_approved_state()

    message_id = service.send(
        state=state,
        account_id="account-001",
    )

    assert message_id == "fake-message-001"
    assert len(provider.sent_messages) == 1

    sent_message = provider.sent_messages[0]["message"]

    assert sent_message["to"] == ["approved@example.com"]
    assert sent_message["subject"] == "Project update"
    assert sent_message["body"] == "Here is the project update."


def test_unapproved_workflow_cannot_send():
    provider = FakeEmailProvider()
    service = EmailSendService(provider)

    state = make_approved_state()
    state.status = EmailWorkflowStatus.SEND_APPROVAL

    with pytest.raises(
        ValueError,
        match="not approved for sending",
    ):
        service.send(
            state=state,
            account_id="account-001",
        )

    assert provider.sent_messages == []


def test_rejected_approval_cannot_send():
    provider = FakeEmailProvider()
    service = EmailSendService(provider)

    state = make_approved_state()
    state.send_approval_decision.status = ApprovalStatus.REJECTED

    with pytest.raises(
        ValueError,
        match="was not approved",
    ):
        service.send(
            state=state,
            account_id="account-001",
        )

    assert provider.sent_messages == []


def test_modified_draft_cannot_be_sent_after_approval():
    provider = FakeEmailProvider()
    service = EmailSendService(provider)
    state = make_approved_state()

    state.draft.body = "Changed after approval."

    with pytest.raises(
        ValueError,
        match="Draft changed after approval",
    ):
        service.send(state=state, account_id="account-001")

    assert provider.sent_messages == []
    assert state.status == EmailWorkflowStatus.SEND_APPROVAL
    assert state.send_approval_decision is None
    assert state.approved_draft_fingerprint is None

from app.schemas.recipient import (
    RecipientCandidate,
    RecipientVerificationStatus,
)
from app.services.recipient_verification import (
    RecipientVerificationService,
)


def make_candidate() -> RecipientCandidate:
    return RecipientCandidate(
        name="John Doe",
        email="john@example.com",
        source="research",
        confidence=0.90,
        reason="Found from approved research context.",
    )


def test_create_verification_request():
    service = RecipientVerificationService()

    request = service.create_request(
        request_id="recipient-approval-123",
        recipients=[make_candidate()],
        requested_by="user-123",
    )

    assert request.request_id == "recipient-approval-123"
    assert request.status == RecipientVerificationStatus.PENDING
    assert request.requested_by == "user-123"
    assert len(request.recipients) == 1


def test_approve_recipient_list():
    service = RecipientVerificationService()

    request = service.create_request(
        request_id="recipient-approval-123",
        recipients=[make_candidate()],
        requested_by="user-123",
    )

    decision = service.approve(
        request=request,
        decided_by="user-123",
        approved_recipients=request.recipients,
        comment="Recipient verified.",
    )

    assert decision.request_id == "recipient-approval-123"
    assert decision.status == RecipientVerificationStatus.APPROVED
    assert decision.decided_by == "user-123"
    assert len(decision.approved_recipients) == 1
    assert decision.comment == "Recipient verified."


def test_reject_recipient_list():
    service = RecipientVerificationService()

    request = service.create_request(
        request_id="recipient-approval-456",
        recipients=[make_candidate()],
        requested_by="user-123",
    )

    decision = service.reject(
        request=request,
        decided_by="user-123",
        comment="Wrong recipient.",
    )

    assert decision.request_id == "recipient-approval-456"
    assert decision.status == RecipientVerificationStatus.REJECTED
    assert decision.decided_by == "user-123"
    assert decision.approved_recipients == []
    assert decision.comment == "Wrong recipient."

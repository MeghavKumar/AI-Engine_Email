from app.schemas.email import ApprovalStatus
from app.services.approval import ApprovalService


def test_approval_request_starts_pending():
    service = ApprovalService()

    request = service.create_request(
        request_id="approval-123",
        requested_by="user-123",
        reason="Email requires human review.",
    )

    assert request.request_id == "approval-123"
    assert request.status == ApprovalStatus.PENDING
    assert request.requested_by == "user-123"


def test_approval_can_be_approved():
    service = ApprovalService()

    request = service.create_request(
        request_id="approval-123",
        requested_by="user-123",
        reason="Email requires human review.",
    )

    decision = service.approve(
        request=request,
        decided_by="user-123",
        comment="Looks good.",
    )

    assert decision.request_id == "approval-123"
    assert decision.status == ApprovalStatus.APPROVED
    assert decision.decided_by == "user-123"
    assert decision.comment == "Looks good."


def test_approval_can_be_rejected():
    service = ApprovalService()

    request = service.create_request(
        request_id="approval-456",
        requested_by="user-123",
        reason="Recipient requires verification.",
    )

    decision = service.reject(
        request=request,
        decided_by="user-123",
        comment="Wrong recipient.",
    )

    assert decision.request_id == "approval-456"
    assert decision.status == ApprovalStatus.REJECTED
    assert decision.decided_by == "user-123"
    assert decision.comment == "Wrong recipient."

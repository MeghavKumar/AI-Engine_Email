from app.schemas.email import (
    ApprovalDecision,
    ApprovalRequest,
    ApprovalStatus,
)


class ApprovalService:
    """Manage human approval decisions."""

    def create_request(
        self,
        request_id: str,
        requested_by: str,
        reason: str,
    ) -> ApprovalRequest:
        return ApprovalRequest(
            request_id=request_id,
            requested_by=requested_by,
            reason=reason,
        )

    def approve(
        self,
        request: ApprovalRequest,
        decided_by: str,
        comment: str | None = None,
    ) -> ApprovalDecision:
        return ApprovalDecision(
            request_id=request.request_id,
            status=ApprovalStatus.APPROVED,
            decided_by=decided_by,
            comment=comment,
        )

    def reject(
        self,
        request: ApprovalRequest,
        decided_by: str,
        comment: str | None = None,
    ) -> ApprovalDecision:
        return ApprovalDecision(
            request_id=request.request_id,
            status=ApprovalStatus.REJECTED,
            decided_by=decided_by,
            comment=comment,
        )
from app.schemas.email import (
    ApprovalDecision,
    ApprovalRequest,
    ApprovalStatus,
)


class ApprovalService:
    """Manage human approval decisions."""

    def create_request(
        self,
        request_id: str,
        requested_by: str,
        reason: str,
    ) -> ApprovalRequest:
        return ApprovalRequest(
            request_id=request_id,
            requested_by=requested_by,
            reason=reason,
        )

    def approve(
        self,
        request: ApprovalRequest,
        decided_by: str,
        comment: str | None = None,
    ) -> ApprovalDecision:
        return ApprovalDecision(
            request_id=request.request_id,
            status=ApprovalStatus.APPROVED,
            decided_by=decided_by,
            comment=comment,
        )

    def reject(
        self,
        request: ApprovalRequest,
        decided_by: str,
        comment: str | None = None,
    ) -> ApprovalDecision:
        return ApprovalDecision(
            request_id=request.request_id,
            status=ApprovalStatus.REJECTED,
            decided_by=decided_by,
            comment=comment,
        )

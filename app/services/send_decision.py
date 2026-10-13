from app.schemas.email import ApprovalDecision, ApprovalStatus
from app.schemas.workflow import EmailWorkflowState, EmailWorkflowStatus
from app.services.approval import ApprovalService
from app.services.draft_integrity import draft_fingerprint


class SendDecisionService:
    """Process the human decision for an email send approval."""

    def __init__(self, approval_service: ApprovalService | None = None):
        self.approval_service = approval_service or ApprovalService()

    def approve(
        self,
        state: EmailWorkflowState,
        decided_by: str,
        comment: str | None = None,
    ) -> ApprovalDecision:
        """Approve only the exact draft submitted for approval."""

        request = self._require_pending_request(state)
        if (
            state.approved_draft_fingerprint is None
            or state.approved_draft_fingerprint != draft_fingerprint(state)
        ):
            self._invalidate_send_approval(state)
            raise ValueError(
                "Draft changed after send approval was requested; request approval again."
            )

        decision = self.approval_service.approve(
            request=request,
            decided_by=decided_by,
            comment=comment,
        )
        state.send_approval_decision = decision
        state.status = EmailWorkflowStatus.READY_TO_SEND
        state.blocked_reason = None
        return decision

    def reject(
        self,
        state: EmailWorkflowState,
        decided_by: str,
        comment: str | None = None,
    ) -> ApprovalDecision:
        """Reject the email send request."""

        request = self._require_pending_request(state)
        decision = self.approval_service.reject(
            request=request,
            decided_by=decided_by,
            comment=comment,
        )
        state.send_approval_decision = decision
        state.status = EmailWorkflowStatus.BLOCKED
        state.blocked_reason = comment or "Email send approval was rejected."
        return decision

    def _require_pending_request(self, state: EmailWorkflowState):
        """Ensure the workflow has a pending send approval request."""

        if state.status != EmailWorkflowStatus.SEND_APPROVAL:
            raise ValueError(
                "Email workflow must be waiting for send approval."
            )
        request = state.send_approval_request
        if request is None:
            raise ValueError("Send approval request is missing.")
        if request.status != ApprovalStatus.PENDING:
            raise ValueError("Send approval request has already been decided.")
        return request

    @staticmethod
    def _invalidate_send_approval(state: EmailWorkflowState) -> None:
        state.send_approval_request = None
        state.send_approval_decision = None
        state.approved_draft_fingerprint = None
        state.status = EmailWorkflowStatus.SEND_APPROVAL
        state.blocked_reason = (
            "Draft changed after approval was requested; new approval is required."
        )
        if state.original_thread_subject is not None:
            state.subject_change_approval_request = None
            state.subject_change_approval_decision = None
            state.subject_change_approval_fingerprint = None

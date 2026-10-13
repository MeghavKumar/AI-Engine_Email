"""Human approval for changing the subject of an existing email thread."""

from app.schemas.email import ApprovalDecision, ApprovalRequest, ApprovalStatus
from app.schemas.workflow import EmailWorkflowState, EmailWorkflowStatus
from app.services.draft_integrity import draft_fingerprint


def normalize_subject(subject: str) -> str:
    """Ignore whitespace differences and leading Re: prefixes."""
    normalized = " ".join(subject.split()).strip()
    while normalized[:3].casefold() == "re:":
        normalized = normalized[3:].lstrip()
    return normalized.casefold()


class SubjectChangeApprovalService:
    """Manage the approval gate for changed reply subjects."""

    @staticmethod
    def requires_approval(state: EmailWorkflowState) -> bool:
        if state.draft is None or state.original_thread_subject is None:
            return False
        return normalize_subject(
            state.original_thread_subject
        ) != normalize_subject(state.draft.subject)

    def create_request(
        self,
        state: EmailWorkflowState,
        request_id: str,
        requested_by: str,
    ) -> ApprovalRequest:
        if state.status != EmailWorkflowStatus.SEND_APPROVAL:
            raise ValueError("Pre-send validation must pass before subject approval.")
        if state.draft is None:
            raise ValueError("A draft is required for subject-change approval.")
        if state.original_thread_subject is None:
            raise ValueError(
                "The original thread subject is required for subject-change approval."
            )
        if not self.requires_approval(state):
            raise ValueError(
                "Subject-change approval is not required for an unchanged subject."
            )

        request = ApprovalRequest(
            request_id=request_id,
            requested_by=requested_by,
            reason=(
                "Approve changing the reply subject from "
                f"{state.original_thread_subject!r} to {state.draft.subject!r}."
            ),
        )
        state.subject_change_approval_request = request
        state.subject_change_approval_decision = None
        state.subject_change_approval_fingerprint = draft_fingerprint(state)
        return request

    def approve(
        self,
        state: EmailWorkflowState,
        decided_by: str,
        comment: str | None = None,
    ) -> ApprovalDecision:
        request = self._require_pending_request(state)
        self._ensure_draft_unchanged(state)
        decision = ApprovalDecision(
            request_id=request.request_id,
            status=ApprovalStatus.APPROVED,
            decided_by=decided_by,
            comment=comment,
        )
        state.subject_change_approval_decision = decision
        return decision

    def reject(
        self,
        state: EmailWorkflowState,
        decided_by: str,
        comment: str | None = None,
    ) -> ApprovalDecision:
        request = self._require_pending_request(state)
        self._ensure_draft_unchanged(state)
        decision = ApprovalDecision(
            request_id=request.request_id,
            status=ApprovalStatus.REJECTED,
            decided_by=decided_by,
            comment=comment,
        )
        state.subject_change_approval_decision = decision
        state.status = EmailWorkflowStatus.BLOCKED
        state.blocked_reason = "The subject change was rejected by a human reviewer."
        return decision

    @staticmethod
    def _require_pending_request(
        state: EmailWorkflowState,
    ) -> ApprovalRequest:
        request = state.subject_change_approval_request
        if (
            state.status != EmailWorkflowStatus.SEND_APPROVAL
            or request is None
            or request.status != ApprovalStatus.PENDING
        ):
            raise ValueError("Workflow is not waiting for subject-change approval.")
        return request

    @staticmethod
    def _ensure_draft_unchanged(state: EmailWorkflowState) -> None:
        if (
            state.subject_change_approval_fingerprint is None
            or state.subject_change_approval_fingerprint != draft_fingerprint(state)
        ):
            state.subject_change_approval_request = None
            state.subject_change_approval_decision = None
            state.subject_change_approval_fingerprint = None
            raise ValueError(
                "Draft changed after subject approval was requested; request approval again."
            )

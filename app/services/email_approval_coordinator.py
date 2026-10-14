"""Coordinate validation and the separate email approval stages."""

from app.schemas.email import ApprovalDecision, ApprovalRequest
from app.schemas.workflow import EmailWorkflowState, EmailWorkflowStatus
from app.services.pre_send_workflow import PreSendWorkflowService
from app.services.send_approval import SendApprovalService
from app.services.send_decision import SendDecisionService
from app.services.subject_change_approval import SubjectChangeApprovalService


class EmailApprovalCoordinator:
    """Route a validated draft through the required human approval gates.

    This service does not send email or persist workflow state. Callers remain
    responsible for persisting state changes and invoking the send service
    only after the send decision has been approved.
    """

    def __init__(
        self,
        pre_send_workflow: PreSendWorkflowService | None = None,
        subject_approval: SubjectChangeApprovalService | None = None,
        send_approval: SendApprovalService | None = None,
        send_decision: SendDecisionService | None = None,
    ) -> None:
        self.pre_send_workflow = pre_send_workflow or PreSendWorkflowService()
        self.subject_approval = subject_approval or SubjectChangeApprovalService()
        self.send_approval = send_approval or SendApprovalService()
        self.send_decision = send_decision or SendDecisionService()

    def validate_and_request_approval(
        self,
        state: EmailWorkflowState,
        request_id: str,
        requested_by: str,
    ) -> ApprovalRequest | None:
        """Validate all gates, then request the next required approval.

        Returns None when validation blocks the workflow. Changed thread
        subjects require a separate approval before normal send approval.
        """
        self.pre_send_workflow.validate(state)

        if state.status != EmailWorkflowStatus.SEND_APPROVAL:
            return None

        if self.subject_approval.requires_approval(state):
            return self.subject_approval.create_request(
                state=state,
                request_id=request_id,
                requested_by=requested_by,
            )

        return self.send_approval.create_request(
            state=state,
            request_id=request_id,
            requested_by=requested_by,
        )

    def request_send_approval(
        self,
        state: EmailWorkflowState,
        request_id: str,
        requested_by: str,
    ) -> ApprovalRequest:
        """Request send approval after any required subject approval."""
        return self.send_approval.create_request(
            state=state,
            request_id=request_id,
            requested_by=requested_by,
        )

    def approve_subject_change(
        self,
        state: EmailWorkflowState,
        decided_by: str,
        comment: str | None = None,
    ) -> ApprovalDecision:
        return self.subject_approval.approve(
            state=state,
            decided_by=decided_by,
            comment=comment,
        )

    def reject_subject_change(
        self,
        state: EmailWorkflowState,
        decided_by: str,
        comment: str | None = None,
    ) -> ApprovalDecision:
        return self.subject_approval.reject(
            state=state,
            decided_by=decided_by,
            comment=comment,
        )

    def approve_send(
        self,
        state: EmailWorkflowState,
        decided_by: str,
        comment: str | None = None,
    ) -> ApprovalDecision:
        return self.send_decision.approve(
            state=state,
            decided_by=decided_by,
            comment=comment,
        )

    def reject_send(
        self,
        state: EmailWorkflowState,
        decided_by: str,
        comment: str | None = None,
    ) -> ApprovalDecision:
        return self.send_decision.reject(
            state=state,
            decided_by=decided_by,
            comment=comment,
        )

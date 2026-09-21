from app.schemas.reminder import (
    ReminderApprovalStatus,
    ReminderDraft,
)
from app.schemas.reminder_workflow import (
    ReminderWorkflowState,
    ReminderWorkflowStatus,
)
from app.services.reminder_security import ReminderSecurityService
from app.services.attachment_verification import (
    AttachmentVerificationService,
)
from app.services.reminder_approval import ReminderApprovalService


class ReminderWorkflowService:
    """Orchestrate the reminder validation and approval workflow."""

    def __init__(
        self,
        security_service: ReminderSecurityService | None = None,
        attachment_service: AttachmentVerificationService | None = None,
        approval_service: ReminderApprovalService | None = None,
    ):
        self.security_service = (
            security_service or ReminderSecurityService()
        )
        self.attachment_service = (
            attachment_service or AttachmentVerificationService()
        )
        self.approval_service = (
            approval_service or ReminderApprovalService()
        )

    def create_state(
        self,
        workflow_id: str,
        reminder: ReminderDraft,
    ) -> ReminderWorkflowState:
        """Create the initial reminder workflow state."""

        return ReminderWorkflowState(
            workflow_id=workflow_id,
            status=ReminderWorkflowStatus.DRAFT_CREATED,
            reminder=reminder,
        )

    def inspect_security(
        self,
        state: ReminderWorkflowState,
    ) -> ReminderWorkflowState:
        """Run the reminder through the security gateway."""

        if state.reminder is None:
            return self._block(
                state,
                "Reminder draft is missing.",
            )

        state.status = ReminderWorkflowStatus.SECURITY_CHECK

        assessment = self.security_service.inspect(
            state.reminder
        )

        state.security_assessment = assessment

        if not assessment.safe:
            return self._block(
                state,
                "Security assessment did not approve the reminder.",
            )

        return state

    def verify_attachments(
        self,
        state: ReminderWorkflowState,
        available_attachments: list[str] | None = None,
    ) -> ReminderWorkflowState:
        """Verify any attachments required by the reminder."""

        if state.reminder is None:
            return self._block(
                state,
                "Reminder draft is missing.",
            )

        if state.security_assessment is None:
            return self._block(
                state,
                "Security assessment has not been completed.",
            )

        if not state.security_assessment.safe:
            return self._block(
                state,
                "Security assessment did not approve the reminder.",
            )

        state.status = ReminderWorkflowStatus.ATTACHMENT_VERIFICATION

        result = self.attachment_service.verify(
            required=state.reminder.attachment_required,
            required_attachments=state.reminder.attachment_names,
            available_attachments=available_attachments,
        )

        state.attachment_verification_result = result

        return state

    def request_approval(
        self,
        state: ReminderWorkflowState,
        requested_by: str,
        reason: str,
    ) -> ReminderWorkflowState:
        """Create a human approval request for a validated reminder."""

        if state.reminder is None:
            return self._block(
                state,
                "Reminder draft is missing.",
            )

        if state.security_assessment is None:
            return self._block(
                state,
                "Security assessment has not been completed.",
            )

        if not state.security_assessment.safe:
            return self._block(
                state,
                "Security assessment did not approve the reminder.",
            )

        if state.attachment_verification_result is None:
            return self._block(
                state,
                "Attachment verification has not been completed.",
            )

        if state.attachment_verification_result.status not in {
            "NOT_REQUIRED",
            "VERIFIED",
        }:
            return self._block(
                state,
                "Required attachments are not verified.",
            )

        try:
            request = self.approval_service.create_request(
                reminder=state.reminder,
                requested_by=requested_by,
                reason=reason,
            )
        except ValueError as exc:
            return self._block(state, str(exc))

        state.approval_request = request
        state.status = ReminderWorkflowStatus.APPROVAL
        state.blocked_reason = None

        return state

    def apply_approval_decision(
        self,
        state: ReminderWorkflowState,
        decision,
    ) -> ReminderWorkflowState:
        """Apply a human approval decision to the reminder workflow."""

        if state.reminder is None:
            return self._block(
                state,
                "Reminder draft is missing.",
            )

        if state.approval_request is None:
            return self._block(
                state,
                "Reminder approval request has not been created.",
            )

        try:
            reminder = self.approval_service.apply_decision(
                reminder=state.reminder,
                request=state.approval_request,
                decision=decision,
            )
        except ValueError as exc:
            return self._block(state, str(exc))

        state.reminder = reminder
        state.approval_decision = decision

        if decision.status == ReminderApprovalStatus.APPROVED:
            state.status = ReminderWorkflowStatus.READY_TO_SEND
            state.blocked_reason = None
        else:
            state.status = ReminderWorkflowStatus.BLOCKED
            state.blocked_reason = "Reminder approval was rejected."

        return state

    def _block(
        self,
        state: ReminderWorkflowState,
        reason: str,
    ) -> ReminderWorkflowState:
        """Mark the reminder workflow as blocked."""

        state.status = ReminderWorkflowStatus.BLOCKED
        state.blocked_reason = reason

        return state

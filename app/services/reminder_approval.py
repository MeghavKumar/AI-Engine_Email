from uuid import uuid4

from app.schemas.reminder import (
    ReminderApprovalDecision,
    ReminderApprovalRequest,
    ReminderApprovalStatus,
    ReminderDraft,
    ReminderStatus,
)


class ReminderApprovalService:
    """Manage human approval for AI-generated reminder emails."""

    def create_request(
        self,
        reminder: ReminderDraft,
        requested_by: str,
        reason: str,
    ) -> ReminderApprovalRequest:
        if reminder.status != ReminderStatus.DRAFT:
            raise ValueError(
                "Only draft reminders can enter the approval process."
            )

        return ReminderApprovalRequest(
            request_id=str(uuid4()),
            requested_by=requested_by,
            reason=reason,
        )

    def apply_decision(
        self,
        reminder: ReminderDraft,
        request: ReminderApprovalRequest,
        decision: ReminderApprovalDecision,
    ) -> ReminderDraft:
        if decision.request_id != request.request_id:
            raise ValueError(
                "Approval decision does not match the approval request."
            )

        if request.status != ReminderApprovalStatus.PENDING:
            raise ValueError(
                "Approval request has already been decided."
            )

        if decision.status == ReminderApprovalStatus.APPROVED:
            reminder.status = ReminderStatus.APPROVED
            return reminder

        if decision.status == ReminderApprovalStatus.REJECTED:
            reminder.status = ReminderStatus.REJECTED
            return reminder

        raise ValueError(
            "Reminder approval decision must be APPROVED or REJECTED."
        )

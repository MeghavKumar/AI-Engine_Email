from pathlib import Path

from app.schemas.email_attachment import EmailAttachment
from app.schemas.reminder_workflow import (
    ReminderWorkflowState,
    ReminderWorkflowStatus,
)
from app.services.workflow_persistence import WorkflowPersistenceService


def test_serialize_reminder_workflow_state():
    service = WorkflowPersistenceService()

    state = ReminderWorkflowState(
        workflow_id="workflow-123",
        status=ReminderWorkflowStatus.DRAFT_CREATED,
    )

    data = service.serialize(state)

    assert data["workflow_id"] == "workflow-123"
    assert data["status"] == "DRAFT_CREATED"


def test_deserialize_reminder_workflow_state():
    service = WorkflowPersistenceService()

    data = {
        "workflow_id": "workflow-123",
        "status": "DRAFT_CREATED",
        "reminder": None,
        "security_assessment": None,
        "attachment_verification_result": None,
        "attachment_action_request": None,
        "attachments": [],
        "approval_request": None,
        "approval_decision": None,
        "blocked_reason": None,
    }

    state = service.deserialize(
        data,
        ReminderWorkflowState,
    )

    assert isinstance(state, ReminderWorkflowState)
    assert state.workflow_id == "workflow-123"
    assert state.status == ReminderWorkflowStatus.DRAFT_CREATED


def test_reminder_workflow_state_round_trip_preserves_attachment():
    service = WorkflowPersistenceService()

    attachment = EmailAttachment(
        filename="document.pdf",
        content_type="application/pdf",
        file_path=Path("/tmp/document.pdf"),
    )

    original = ReminderWorkflowState(
        workflow_id="workflow-456",
        status=ReminderWorkflowStatus.READY_TO_SEND,
        attachments=[attachment],
    )

    data = service.serialize(original)

    restored = service.deserialize(
        data,
        ReminderWorkflowState,
    )

    assert restored == original
    assert restored.attachments[0].filename == "document.pdf"
    assert restored.attachments[0].file_path == Path("/tmp/document.pdf")

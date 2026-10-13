import pytest

from app.schemas.email import ApprovalStatus, EmailDraft
from app.schemas.workflow import EmailWorkflowState, EmailWorkflowStatus
from app.services.send_approval import SendApprovalService
from app.services.subject_change_approval import (
    SubjectChangeApprovalService,
)


def make_state(original_subject="Project update", draft_subject="Project update"):
    return EmailWorkflowState(
        workflow_id="subject-workflow-001",
        status=EmailWorkflowStatus.SEND_APPROVAL,
        original_thread_subject=original_subject,
        draft=EmailDraft(
            to=["recipient@example.com"],
            subject=draft_subject,
            body="Here is the update.",
            confidence=0.95,
        ),
    )


def test_unchanged_subject_does_not_require_subject_approval():
    state = make_state(
        original_subject="Re: Project update",
        draft_subject="Project update",
    )
    service = SubjectChangeApprovalService()

    assert service.requires_approval(state) is False

    request = SendApprovalService().create_request(
        state,
        request_id="send-001",
        requested_by="user-001",
    )
    assert request.request_id == "send-001"
    assert state.approved_draft_fingerprint is not None
    assert state.subject_change_approval_request is None


def test_changed_subject_requires_separate_approval_before_send_approval():
    state = make_state(draft_subject="Urgent project update")
    subject_service = SubjectChangeApprovalService()

    assert subject_service.requires_approval(state) is True

    with pytest.raises(ValueError, match="Subject change requires explicit approval"):
        SendApprovalService().create_request(
            state,
            request_id="send-001",
            requested_by="user-001",
        )

    subject_service.create_request(
        state,
        request_id="subject-001",
        requested_by="user-001",
    )
    decision = subject_service.approve(state, decided_by="reviewer-001")

    assert decision.status == ApprovalStatus.APPROVED

    send_request = SendApprovalService().create_request(
        state,
        request_id="send-002",
        requested_by="user-001",
    )
    assert send_request.request_id == "send-002"


def test_rejected_subject_change_blocks_workflow():
    state = make_state(draft_subject="Urgent project update")
    service = SubjectChangeApprovalService()

    service.create_request(
        state,
        request_id="subject-001",
        requested_by="user-001",
    )
    decision = service.reject(
        state,
        decided_by="reviewer-001",
        comment="Keep the existing thread subject.",
    )

    assert decision.status == ApprovalStatus.REJECTED
    assert state.status == EmailWorkflowStatus.BLOCKED

    with pytest.raises(ValueError, match="pre-send validation"):
        SendApprovalService().create_request(
            state,
            request_id="send-001",
            requested_by="user-001",
        )


def test_changed_draft_invalidates_pending_subject_approval():
    state = make_state(draft_subject="Urgent project update")
    service = SubjectChangeApprovalService()

    service.create_request(
        state,
        request_id="subject-001",
        requested_by="user-001",
    )
    state.draft.body = "This body changed after the request."

    with pytest.raises(ValueError, match="Draft changed after subject approval"):
        service.approve(state, decided_by="reviewer-001")

    assert state.subject_change_approval_request is None
    assert state.subject_change_approval_decision is None
    assert state.subject_change_approval_fingerprint is None

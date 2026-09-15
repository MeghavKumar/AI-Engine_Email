import pytest

from app.schemas.attachment import (
    AttachmentVerificationResult,
    AttachmentVerificationStatus,
)
from app.services.attachment_action import (
    AttachmentActionService,
)


def test_missing_attachments_create_human_action_request():
    service = AttachmentActionService()

    verification_result = AttachmentVerificationResult(
        status=AttachmentVerificationStatus.MISSING,
        required=True,
        attachment_names=[
            "project-report.pdf",
            "budget.xlsx",
        ],
        missing_attachments=[
            "budget.xlsx",
        ],
        reason="One or more required attachments are missing.",
    )

    request = service.create_request(
        request_id="attachment-001",
        verification_result=verification_result,
    )

    assert request.request_id == "attachment-001"
    assert request.status == AttachmentVerificationStatus.MISSING
    assert request.requires_human_action is True
    assert request.attachment_names == ["budget.xlsx"]


def test_verified_attachments_do_not_create_request():
    service = AttachmentActionService()

    verification_result = AttachmentVerificationResult(
        status=AttachmentVerificationStatus.VERIFIED,
        required=True,
        attachment_names=["project-report.pdf"],
        reason="All required attachments are present.",
    )

    with pytest.raises(ValueError, match="only required"):
        service.create_request(
            request_id="attachment-002",
            verification_result=verification_result,
        )


def test_not_required_attachments_do_not_create_request():
    service = AttachmentActionService()

    verification_result = AttachmentVerificationResult(
        status=AttachmentVerificationStatus.NOT_REQUIRED,
        required=False,
        reason="No attachment is required.",
    )

    with pytest.raises(ValueError, match="only required"):
        service.create_request(
            request_id="attachment-003",
            verification_result=verification_result,
        )


def test_missing_status_requires_missing_attachment_names():
    service = AttachmentActionService()

    verification_result = AttachmentVerificationResult(
        status=AttachmentVerificationStatus.MISSING,
        required=True,
        attachment_names=[],
        missing_attachments=[],
        reason="Attachments are missing.",
    )

    with pytest.raises(ValueError, match="cannot be empty"):
        service.create_request(
            request_id="attachment-004",
            verification_result=verification_result,
        )

from app.schemas.attachment import (
    AttachmentVerificationRequest,
    AttachmentVerificationResult,
    AttachmentVerificationStatus,
)


def test_attachment_not_required():
    result = AttachmentVerificationResult(
        status=AttachmentVerificationStatus.NOT_REQUIRED,
        required=False,
        reason="No attachment is required.",
    )

    assert result.status == AttachmentVerificationStatus.NOT_REQUIRED
    assert result.required is False
    assert result.attachment_names == []
    assert result.missing_attachments == []


def test_attachment_is_verified():
    result = AttachmentVerificationResult(
        status=AttachmentVerificationStatus.VERIFIED,
        required=True,
        attachment_names=["project-report.pdf"],
        reason="Required attachment is present.",
    )

    assert result.status == AttachmentVerificationStatus.VERIFIED
    assert result.required is True
    assert result.attachment_names == ["project-report.pdf"]
    assert result.missing_attachments == []


def test_attachment_is_missing():
    result = AttachmentVerificationResult(
        status=AttachmentVerificationStatus.MISSING,
        required=True,
        attachment_names=["project-report.pdf"],
        missing_attachments=["project-report.pdf"],
        reason="Required attachment is missing.",
    )

    assert result.status == AttachmentVerificationStatus.MISSING
    assert result.required is True
    assert result.missing_attachments == ["project-report.pdf"]


def test_missing_attachment_creates_human_action_request():
    request = AttachmentVerificationRequest(
        request_id="attachment-123",
        attachment_names=["project-report.pdf"],
    )

    assert request.request_id == "attachment-123"
    assert request.status == AttachmentVerificationStatus.MISSING
    assert request.requires_human_action is True
    assert request.attachment_names == ["project-report.pdf"]

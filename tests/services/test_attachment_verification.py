from app.schemas.attachment import AttachmentVerificationStatus
from app.services.attachment_verification import (
    AttachmentVerificationService,
)


def test_attachment_not_required():
    service = AttachmentVerificationService()

    result = service.verify(
        required=False,
    )

    assert result.status == AttachmentVerificationStatus.NOT_REQUIRED
    assert result.required is False
    assert result.missing_attachments == []


def test_all_required_attachments_are_present():
    service = AttachmentVerificationService()

    result = service.verify(
        required=True,
        required_attachments=[
            "project-report.pdf",
            "budget.xlsx",
        ],
        available_attachments=[
            "project-report.pdf",
            "budget.xlsx",
        ],
    )

    assert result.status == AttachmentVerificationStatus.VERIFIED
    assert result.required is True
    assert result.missing_attachments == []


def test_missing_required_attachment():
    service = AttachmentVerificationService()

    result = service.verify(
        required=True,
        required_attachments=[
            "project-report.pdf",
            "budget.xlsx",
        ],
        available_attachments=[
            "project-report.pdf",
        ],
    )

    assert result.status == AttachmentVerificationStatus.MISSING
    assert result.required is True
    assert result.missing_attachments == ["budget.xlsx"]


def test_attachment_matching_is_case_insensitive():
    service = AttachmentVerificationService()

    result = service.verify(
        required=True,
        required_attachments=["Project-Report.PDF"],
        available_attachments=["project-report.pdf"],
    )

    assert result.status == AttachmentVerificationStatus.VERIFIED
    assert result.missing_attachments == []


def test_multiple_missing_attachments():
    service = AttachmentVerificationService()

    result = service.verify(
        required=True,
        required_attachments=[
            "report.pdf",
            "budget.xlsx",
            "presentation.pptx",
        ],
        available_attachments=[
            "report.pdf",
        ],
    )

    assert result.status == AttachmentVerificationStatus.MISSING
    assert result.missing_attachments == [
        "budget.xlsx",
        "presentation.pptx",
    ]

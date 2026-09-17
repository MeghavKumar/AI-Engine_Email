from pathlib import Path

import pytest

from app.services.attachment_resolution import (
    AttachmentResolutionService,
)


def test_resolves_existing_attachment(tmp_path: Path):
    attachment = tmp_path / "report.pdf"
    attachment.write_bytes(b"fake pdf content")

    service = AttachmentResolutionService()

    result = service.resolve(
        attachment_names=["report.pdf"],
        attachment_directory=tmp_path,
    )

    assert len(result) == 1
    assert result[0].filename == "report.pdf"
    assert result[0].content_type == "application/pdf"
    assert result[0].file_path == attachment


def test_missing_attachment_raises_error(tmp_path: Path):
    service = AttachmentResolutionService()

    with pytest.raises(
        ValueError,
        match="Attachment file does not exist",
    ):
        service.resolve(
            attachment_names=["missing.pdf"],
            attachment_directory=tmp_path,
        )


def test_invalid_directory_raises_error(tmp_path: Path):
    service = AttachmentResolutionService()

    missing_directory = tmp_path / "does-not-exist"

    with pytest.raises(
        ValueError,
        match="Attachment directory does not exist",
    ):
        service.resolve(
            attachment_names=["report.pdf"],
            attachment_directory=missing_directory,
        )


def test_rejects_attachment_outside_directory(tmp_path: Path):
    attachment_directory = tmp_path / "attachments"
    attachment_directory.mkdir()

    outside_file = tmp_path / "secret.txt"
    outside_file.write_text("private content")

    service = AttachmentResolutionService()

    with pytest.raises(
        ValueError,
        match="outside the attachment directory",
    ):
        service.resolve(
            attachment_names=["../secret.txt"],
            attachment_directory=attachment_directory,
        )

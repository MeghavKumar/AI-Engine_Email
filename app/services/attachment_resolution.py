import mimetypes
from pathlib import Path

from app.schemas.email_attachment import EmailAttachment


class AttachmentResolutionService:
    """Resolve verified attachment names into sendable files."""

    def resolve(
        self,
        attachment_names: list[str],
        attachment_directory: str | Path,
    ) -> list[EmailAttachment]:
        """Resolve attachment names to existing files."""

        directory = Path(attachment_directory)

        if not directory.is_dir():
            raise ValueError(
                f"Attachment directory does not exist: {directory}"
            )

        directory = directory.resolve()
        attachments = []

        for filename in attachment_names:
            file_path = (directory / filename).resolve()

            if directory not in file_path.parents:
                raise ValueError(
                    f"Attachment path is outside the attachment directory: "
                    f"{filename}"
                )

            if not file_path.is_file():
                raise ValueError(
                    f"Attachment file does not exist: {file_path}"
                )

            content_type, _ = mimetypes.guess_type(
                file_path.name
            )

            attachments.append(
                EmailAttachment(
                    filename=file_path.name,
                    content_type=(
                        content_type
                        or "application/octet-stream"
                    ),
                    file_path=file_path,
                )
            )

        return attachments

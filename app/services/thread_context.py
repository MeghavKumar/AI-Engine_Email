from app.db.repositories.email_message import EmailMessageRepository


class ThreadContextService:
    """Build bounded, transient context from persisted thread messages."""

    def __init__(self, message_repository: EmailMessageRepository):
        self.message_repository = message_repository

    def build_context(
        self,
        *,
        account_id: int,
        thread_id: int,
        max_messages: int = 10,
        max_chars: int = 12000,
    ) -> dict:
        """Return chronological thread context within message and text limits.

        max_chars bounds the combined characters in message metadata and
        bodies. Newer messages are prioritized if the character budget
        cannot accommodate the entire retrieved history.
        """
        if max_messages < 1:
            raise ValueError("max_messages must be at least 1")
        if max_chars < 1:
            raise ValueError("max_chars must be at least 1")

        messages = self.message_repository.list_by_thread(
            account_id=account_id,
            thread_id=thread_id,
            limit=max_messages,
        )

        selected = []
        remaining_chars = max_chars
        truncated = False

        # Prioritize the newest messages, then restore chronological order.
        for message in reversed(messages):
            sender = message.sender_email or ""
            subject = message.subject or ""
            body = message.body_text or ""
            received_at = (
                message.received_at.isoformat()
                if message.received_at is not None
                else None
            )

            metadata_chars = len(sender) + len(subject)
            if received_at:
                metadata_chars += len(received_at)

            if metadata_chars >= remaining_chars:
                truncated = True
                continue

            body_budget = remaining_chars - metadata_chars
            if len(body) > body_budget:
                body = body[:body_budget]
                truncated = True

            record = {
                "sender_email": sender,
                "subject": subject,
                "received_at": received_at,
                "body_text": body,
            }

            used_chars = metadata_chars + len(body)
            selected.append(record)
            remaining_chars -= used_chars

            if remaining_chars <= 0:
                truncated = True
                break

        if len(selected) < len(messages):
            truncated = True

        selected.reverse()

        return {
            "account_id": account_id,
            "thread_id": thread_id,
            "messages": selected,
            "truncated": truncated,
        }

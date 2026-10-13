from app.agents.composer import EmailComposer
from app.services.thread_context import ThreadContextService


class EmailCompositionService:
    """Compose email drafts with bounded context from an existing thread."""

    def __init__(
        self,
        composer: EmailComposer,
        thread_context_service: ThreadContextService,
    ) -> None:
        self.composer = composer
        self.thread_context_service = thread_context_service

    def compose_for_thread(
        self,
        *,
        prompt: str,
        account_id: int,
        thread_id: int,
        max_messages: int = 10,
        max_chars: int = 12000,
    ):
        """Build thread context and pass it to the validated email composer."""

        context = self.thread_context_service.build_context(
            account_id=account_id,
            thread_id=thread_id,
            max_messages=max_messages,
            max_chars=max_chars,
        )

        return self.composer.compose(
            prompt=prompt,
            context=context,
        )

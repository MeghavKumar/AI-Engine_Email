from app.agents.composer import EmailComposer
from app.schemas.email import EmailDraft
from app.schemas.research import ResearchResult
from app.services.thread_context import ThreadContextService


class EmailCompositionService:
    """Compose validated drafts using bounded thread and research context."""

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
        research_result: ResearchResult | None = None,
        max_messages: int = 10,
        max_chars: int = 12000,
    ) -> EmailDraft:
        """Build bounded context and return a validated draft without sending."""

        context = self.thread_context_service.build_context(
            account_id=account_id,
            thread_id=thread_id,
            max_messages=max_messages,
            max_chars=max_chars,
        )

        # Keep the existing context structure and add research only when supplied.
        context = dict(context)

        if research_result is not None:
            context["research"] = research_result.model_dump(mode="json")

        return self.composer.compose(
            prompt=prompt,
            context=context,
        )

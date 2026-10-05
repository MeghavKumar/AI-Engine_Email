from uuid import uuid4

from app.agents.research import ResearchAgent
from app.schemas.research import ResearchResult
from app.services.research_run import ResearchRunService


class ResearchExecutionService:
    """Execute research while persisting its lifecycle metadata."""

    def __init__(
        self,
        research_agent: ResearchAgent,
        research_run_service: ResearchRunService,
    ):
        self.research_agent = research_agent
        self.research_run_service = research_run_service

    def research(
        self,
        *,
        account_id: int,
        recipient_email: str,
        limit: int = 20,
        web_query: str | None = None,
    ) -> ResearchResult:
        """Run historical/web research with persisted lifecycle metadata."""

        run_id = str(uuid4())

        research_run = self.research_run_service.create(
            run_id=run_id,
            account_id=account_id,
            research_type="recipient_research",
        )

        self.research_run_service.mark_started(research_run)

        try:
            result = self.research_agent.research(
                account_id=account_id,
                recipient_email=recipient_email,
                limit=limit,
                web_query=web_query,
            )
        except Exception as exc:
            self.research_run_service.mark_error(
                research_run,
                str(exc),
            )
            raise

        self.research_run_service.mark_success(research_run)

        return result

    def research_new_recipient(
        self,
        *,
        account_id: int,
        name: str,
        role: str | None = None,
        organization: str | None = None,
        web_query: str | None = None,
    ) -> ResearchResult:
        """Run new-recipient research with persisted lifecycle metadata."""

        run_id = str(uuid4())

        research_run = self.research_run_service.create(
            run_id=run_id,
            account_id=account_id,
            research_type="new_recipient",
        )

        self.research_run_service.mark_started(research_run)

        try:
            result = self.research_agent.research_new_recipient(
                name=name,
                role=role,
                organization=organization,
                web_query=web_query,
            )
        except Exception as exc:
            self.research_run_service.mark_error(
                research_run,
                str(exc),
            )
            raise

        self.research_run_service.mark_success(research_run)

        return result

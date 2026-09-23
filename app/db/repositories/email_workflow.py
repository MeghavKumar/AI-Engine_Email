from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.email_workflow import EmailWorkflow


class EmailWorkflowRepository:
    """Database repository for persisted email and reminder workflows."""

    def __init__(self, session: Session):
        self.session = session

    def create(
        self,
        workflow_id: str,
        email_account_id: int,
        user_id: str,
        workflow_type: str,
        provider: str,
        status: str,
        state: dict,
        message_id: str | None = None,
        thread_id: str | None = None,
    ) -> EmailWorkflow:
        workflow = EmailWorkflow(
            workflow_id=workflow_id,
            email_account_id=email_account_id,
            user_id=user_id,
            workflow_type=workflow_type,
            provider=provider,
            message_id=message_id,
            thread_id=thread_id,
            status=status,
            state=state,
        )

        self.session.add(workflow)
        self.session.flush()

        return workflow

    def get_by_workflow_id(
        self,
        workflow_id: str,
    ) -> EmailWorkflow | None:
        statement = select(EmailWorkflow).where(
            EmailWorkflow.workflow_id == workflow_id
        )

        return self.session.scalar(statement)

    def update(
        self,
        workflow: EmailWorkflow,
        status: str,
        state: dict,
        message_id: str | None = None,
        thread_id: str | None = None,
    ) -> EmailWorkflow:
        workflow.status = status
        workflow.state = state

        if message_id is not None:
            workflow.message_id = message_id

        if thread_id is not None:
            workflow.thread_id = thread_id

        self.session.flush()

        return workflow

    def close(
        self,
        workflow: EmailWorkflow,
        status: str,
        state: dict,
        closed_at: datetime | None = None,
    ) -> EmailWorkflow:
        workflow.status = status
        workflow.state = state
        workflow.closed_at = closed_at or datetime.now().astimezone()

        self.session.flush()

        return workflow

from pydantic import BaseModel

from app.agents.classifier import EmailClassifier
from app.schemas.email import EmailClassification, TriageDecision
from app.schemas.provider import EmailMessage
from app.services.inbox import InboxService
from app.services.triage import EmailTriageService


class ProcessedEmail(BaseModel):
    message: EmailMessage
    classification: EmailClassification
    triage: TriageDecision


class InboxProcessor:
    """Process inbox messages through classification and triage."""

    def __init__(
        self,
        inbox_service: InboxService,
        classifier: EmailClassifier,
        triage_service: EmailTriageService,
    ):
        self.inbox_service = inbox_service
        self.classifier = classifier
        self.triage_service = triage_service

    def process(
        self,
        account_id: str,
        max_results: int = 25,
    ) -> list[ProcessedEmail]:
        messages = self.inbox_service.get_inbox(
            account_id=account_id,
            max_results=max_results,
        )

        processed: list[ProcessedEmail] = []

        for message in messages:
            classification = self.classifier.classify(message)

            triage = self.triage_service.decide(
                classification
            )

            processed.append(
                ProcessedEmail(
                    message=message,
                    classification=classification,
                    triage=triage,
                )
            )

        return processed

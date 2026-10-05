import json

from app.providers.ai.base import AIProvider
from app.schemas.research import (
    ResearchAssessment,
    ResearchResult,
)
from app.services.mailbox_research import MailboxResearchService


class ResearchAgent:
    """Gather controlled evidence and produce an AI assessment."""

    def __init__(
        self,
        mailbox_research: MailboxResearchService,
        ai_provider: AIProvider,
    ):
        self.mailbox_research = mailbox_research
        self.ai_provider = ai_provider

    def research(
        self,
        *,
        account_id: int,
        recipient_email: str,
        limit: int = 20,
    ) -> ResearchResult:
        """Gather mailbox evidence and assess it with an AI provider."""

        evidence = self.mailbox_research.find_historical_evidence(
            account_id=account_id,
            recipient_email=recipient_email,
            limit=limit,
        )

        if not evidence:
            return ResearchResult(evidence=[])

        evidence_data = [
            item.model_dump(mode="json")
            for item in evidence
        ]

        prompt = self._build_prompt(evidence_data)

        response = self.ai_provider.generate(
            prompt=prompt,
            context={
                "account_id": account_id,
                "recipient_email": recipient_email,
            },
        )

        assessment = ResearchAssessment.model_validate(
            self._parse_response(response)
        )

        return ResearchResult(
            evidence=evidence,
            assessment=assessment,
        )

    def _build_prompt(self, evidence: list[dict]) -> str:
        """Build a constrained research-assessment prompt."""

        return f"""
You are an email research assessment system.

Assess the supplied historical mailbox evidence.

Important rules:
- Use ONLY the supplied evidence.
- Do not invent facts.
- Do not invent email addresses.
- Do not treat historical usage as authorization.
- Clearly distinguish evidence from your assessment.
- Return ONLY valid JSON.
- Do not include markdown.
- Do not add additional fields.

Return exactly this structure:

{{
  "assessment": "Concise assessment based only on the evidence.",
  "confidence": 0.95
}}

Historical evidence:
{json.dumps(evidence, indent=2, default=str)}
""".strip()

    def _parse_response(self, response: str) -> dict:
        """Parse the AI provider's JSON response."""

        cleaned = response.strip()

        if cleaned.startswith("```"):
            cleaned = cleaned.replace("```json", "")
            cleaned = cleaned.replace("```", "")
            cleaned = cleaned.strip()

        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError as exc:
            raise ValueError(
                "AI research assessment returned invalid JSON."
            ) from exc

        if not isinstance(data, dict):
            raise ValueError(
                "AI research assessment must be a JSON object."
            )

        return data

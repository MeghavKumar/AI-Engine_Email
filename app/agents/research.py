import json

from app.providers.ai.base import AIProvider
from app.schemas.research import (
    ResearchAssessment,
    ResearchResult,
    ResearchSourceType,
)
from app.services.mailbox_research import MailboxResearchService
from app.services.web_research import WebResearchService


class ResearchAgent:
    """Gather controlled evidence and produce an AI assessment."""

    def __init__(
        self,
        mailbox_research: MailboxResearchService,
        ai_provider: AIProvider,
        web_research: WebResearchService | None = None,
    ):
        self.mailbox_research = mailbox_research
        self.ai_provider = ai_provider
        self.web_research = web_research

    def research(
        self,
        *,
        account_id: int,
        recipient_email: str,
        limit: int = 20,
        web_query: str | None = None,
        web_source_type: ResearchSourceType = ResearchSourceType.WEB,
    ) -> ResearchResult:
        """Gather controlled evidence and assess it with an AI provider."""

        evidence = self.mailbox_research.find_historical_evidence(
            account_id=account_id,
            recipient_email=recipient_email,
            limit=limit,
        )

        if web_query is not None:
            if self.web_research is None:
                raise ValueError(
                    "WebResearchService is required for web research."
                )

            evidence.extend(
                self.web_research.search(
                    web_query,
                    source_type=web_source_type,
                )
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

    def research_new_recipient(
        self,
        *,
        name: str,
        role: str | None = None,
        organization: str | None = None,
        web_query: str | None = None,
        web_source_type: ResearchSourceType = ResearchSourceType.WEB,
    ) -> ResearchResult:
        """Research a new recipient without inventing contact details."""

        if self.web_research is None:
            raise ValueError(
                "WebResearchService is required for new recipient research."
            )

        query = web_query or " ".join(
            part
            for part in (name, role, organization)
            if part
        )

        evidence = self.web_research.search(
            query,
            source_type=web_source_type,
        )

        if not evidence:
            return ResearchResult(evidence=[])

        evidence_data = [
            item.model_dump(mode="json")
            for item in evidence
        ]

        prompt = self._build_new_recipient_prompt(
            name=name,
            role=role,
            organization=organization,
            evidence=evidence_data,
        )

        response = self.ai_provider.generate(
            prompt=prompt,
            context={
                "research_type": "new_recipient",
                "name": name,
                "role": role,
                "organization": organization,
            },
        )

        assessment = ResearchAssessment.model_validate(
            self._parse_response(response)
        )

        return ResearchResult(
            evidence=evidence,
            assessment=assessment,
        )

    def _build_new_recipient_prompt(
        self,
        *,
        name: str,
        role: str | None,
        organization: str | None,
        evidence: list[dict],
    ) -> str:
        """Build a constrained new-recipient research prompt."""

        return f"""
You are an email recipient research assessment system.

Research target:
- Name: {name}
- Role: {role}
- Organization: {organization}

Assess ONLY the supplied public research evidence.

Important rules:
- Use ONLY the supplied evidence.
- Do not invent facts.
- Do not invent email addresses.
- Do not infer an email address from a naming convention.
- If an email address appears in the evidence, treat it as discovered evidence,
  not as authorization to send.
- Clearly distinguish discovered facts from inference.
- Human verification is required before any recipient can be authorized.
- Return ONLY valid JSON.
- Do not include markdown.
- Do not add additional fields.

Return exactly this structure:

{{
  "assessment": "Concise assessment based only on the supplied evidence.",
  "confidence": 0.95
}}

Research evidence:
{json.dumps(evidence, indent=2, default=str)}
""".strip()

    def _build_prompt(self, evidence: list[dict]) -> str:
        """Build a constrained research-assessment prompt."""

        return f"""
You are an email research assessment system.

Assess the supplied research evidence.

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

Research evidence:
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

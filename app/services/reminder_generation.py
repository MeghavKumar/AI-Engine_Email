import json

from app.providers.ai.base import AIProvider
from app.schemas.reminder import ReminderDraft


class ReminderGenerationService:
    """Generate and validate an AI-created reminder email."""

    def __init__(self, ai_provider: AIProvider):
        self.ai_provider = ai_provider

    def generate(
        self,
        original_subject: str,
        original_body: str,
        recipient_email: str,
        context: dict | None = None,
    ) -> ReminderDraft:
        prompt = self._build_prompt(
            original_subject=original_subject,
            original_body=original_body,
            recipient_email=recipient_email,
            context=context,
        )

        raw_response = self.ai_provider.generate(
            prompt=prompt,
            context=context,
        )

        return self._parse_response(raw_response)

    def _build_prompt(
        self,
        original_subject: str,
        original_body: str,
        recipient_email: str,
        context: dict | None = None,
    ) -> str:
        return f"""
Generate a concise professional follow-up reminder email.

Original subject:
{original_subject}

Original email:
{original_body}

Recipient:
{recipient_email}

Return ONLY valid JSON with these fields:
{{
  "to": ["recipient@example.com"],
  "cc": [],
  "subject": "Follow-up: ...",
  "body": "..."
}}

Do not add commentary outside the JSON.
""".strip()

    def _parse_response(self, raw_response: str) -> ReminderDraft:
        try:
            data = json.loads(raw_response)
        except json.JSONDecodeError as exc:
            raise ValueError(
                "AI reminder response is not valid JSON."
            ) from exc

        try:
            return ReminderDraft.model_validate(data)
        except Exception as exc:
            raise ValueError(
                "AI reminder response failed schema validation."
            ) from exc

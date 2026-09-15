import json

from app.providers.ai.base import AIProvider
from app.schemas.email import EmailDraft


class EmailComposer:
    """Compose structured email drafts using an AI provider."""

    def __init__(self, ai_provider: AIProvider):
        self.ai_provider = ai_provider

    def compose(
        self,
        prompt: str,
        context: dict | None = None,
    ) -> EmailDraft:
        """Generate and validate an email draft."""

        composer_prompt = self._build_prompt(
            prompt=prompt,
            context=context,
        )

        response = self.ai_provider.generate(
            prompt=composer_prompt,
            context=context,
        )

        data = self._parse_response(response)

        return EmailDraft.model_validate(data)

    def _build_prompt(
        self,
        prompt: str,
        context: dict | None = None,
    ) -> str:
        """Build a constrained email composition prompt."""

        context_text = ""

        if context:
            context_text = f"""
Additional context:
{json.dumps(context, indent=2, default=str)}
""".strip()

        return f"""
You are an email composition system.

Create an email draft based on the user's request.

Return ONLY valid JSON using exactly this structure:

{{
  "to": ["recipient@example.com"],
  "cc": [],
  "bcc": [],
  "subject": "Email subject",
  "body": "Email body",
  "attachment_required": false,
  "attachment_names": [],
  "confidence": 0.95
}}

Rules:
- "to" must contain at least one valid email address.
- "cc" and "bcc" may be empty lists.
- subject must not be empty.
- body must not be empty.
- attachment_required must be true only when an attachment is required.
- attachment_names must contain the required attachment names when applicable.
- confidence must be between 0.0 and 1.0.
- do not include markdown.
- do not include explanations.
- do not add additional fields.
- Do not invent recipient email addresses when the user has not provided
  enough information to determine them.

User request:
{prompt}

{context_text}
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
                "AI composer returned invalid JSON."
            ) from exc

        if not isinstance(data, dict):
            raise ValueError(
                "AI composer response must be a JSON object."
            )

        return data

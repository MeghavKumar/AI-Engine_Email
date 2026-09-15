import json

from app.providers.ai.base import AIProvider
from app.schemas.email import EmailClassification
from app.schemas.provider import EmailMessage


class EmailClassifier:
    """Classify emails using an AI provider."""

    def __init__(self, ai_provider: AIProvider):
        self.ai_provider = ai_provider

    def classify(
        self,
        message: EmailMessage,
    ) -> EmailClassification:
        """Classify an email and validate the AI response."""

        prompt = self._build_prompt(message)

        response = self.ai_provider.generate(
            prompt=prompt,
            context={
                "message_id": message.message_id,
                "thread_id": message.thread_id,
            },
        )

        data = self._parse_response(response)

        return EmailClassification.model_validate(data)

    def _build_prompt(self, message: EmailMessage) -> str:
        """Build a constrained classification prompt."""

        return f"""
You are an email classification system.

Classify the email into exactly one category:
- SPAM
- PROMOTION
- ACTION_REQUIRED
- INFORMATIONAL

Classify the priority into exactly one level:
- LOW
- MEDIUM
- HIGH
- URGENT

Determine whether the user needs to take action.

Return ONLY valid JSON using exactly this structure:

{{
  "category": "SPAM",
  "priority": "LOW",
  "requires_action": false,
  "confidence": 0.95
}}

Rules:
- confidence must be a number between 0.0 and 1.0
- do not include markdown
- do not include explanations
- do not add additional fields

Email:
From: {message.sender.email}
Subject: {message.subject}

Body:
{message.body_text}
""".strip()

    def _parse_response(self, response: str) -> dict:
        """Parse the model's JSON response."""

        cleaned = response.strip()

        if cleaned.startswith("```"):
            cleaned = cleaned.replace("```json", "")
            cleaned = cleaned.replace("```", "")
            cleaned = cleaned.strip()

        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError as exc:
            raise ValueError(
                "AI classifier returned invalid JSON."
            ) from exc

        if not isinstance(data, dict):
            raise ValueError(
                "AI classifier response must be a JSON object."
            )

        return data

from app.providers.ai.base import AIProvider
from app.security.pii_redactor import PiiRedactor


class PrivacyBoundaryProvider(AIProvider):
    """Redact PII before forwarding text to an AI provider."""

    def __init__(
        self,
        provider: AIProvider,
        redactor: PiiRedactor | None = None,
    ) -> None:
        self._provider = provider
        self._redactor = (
            redactor if redactor is not None else PiiRedactor()
        )

    def _sanitize(self, value):
        if isinstance(value, str):
            try:
                sanitized = self._redactor.redact(value)
            except Exception:
                # Fail closed without exposing potentially sensitive details.
                raise RuntimeError("provider call blocked") from None

            if not isinstance(sanitized, str):
                raise RuntimeError("provider call blocked")

            return sanitized

        if isinstance(value, dict):
            return {
                key: self._sanitize(item)
                for key, item in value.items()
            }

        if isinstance(value, list):
            return [self._sanitize(item) for item in value]

        if isinstance(value, tuple):
            return tuple(self._sanitize(item) for item in value)

        return value

    def generate(
        self,
        prompt: str,
        context: dict | None = None,
    ) -> str:
        # Sanitize all inputs before making any provider call.
        sanitized_prompt = self._sanitize(prompt)
        sanitized_context = self._sanitize(context)

        return self._provider.generate(
            sanitized_prompt,
            sanitized_context,
        )

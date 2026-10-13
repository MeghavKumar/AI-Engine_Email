from app.providers.ai.base import AIProvider
from app.providers.ai.ollama import OllamaProvider
from app.providers.ai.privacy_boundary import PrivacyBoundaryProvider
from app.security.pii_redactor import PiiRedactor


def create_ai_provider(
    provider: AIProvider | None = None,
    redactor: PiiRedactor | None = None,
) -> AIProvider:
    """Create an AI provider protected by the PII privacy boundary.

    Defaults to Ollama when no provider is supplied. All returned providers
    sanitize prompts and context before forwarding requests.
    """
    underlying_provider = (
        provider if provider is not None else OllamaProvider()
    )

    return PrivacyBoundaryProvider(
        provider=underlying_provider,
        redactor=redactor,
    )

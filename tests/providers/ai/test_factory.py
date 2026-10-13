from app.providers.ai.factory import create_ai_provider
from app.providers.ai.ollama import OllamaProvider
from app.providers.ai.privacy_boundary import PrivacyBoundaryProvider


class FakeAIProvider:
    def __init__(self):
        self.calls = []

    def generate(self, prompt, context=None):
        self.calls.append((prompt, context))
        return "fake response"


class FakeRedactor:
    def redact(self, text):
        return text.replace("alex@example.com", "[REDACTED_EMAIL]")


def test_factory_wraps_injected_provider_with_privacy_boundary():
    underlying = FakeAIProvider()

    provider = create_ai_provider(
        provider=underlying,
        redactor=FakeRedactor(),
    )

    assert isinstance(provider, PrivacyBoundaryProvider)


def test_factory_redacts_prompt_and_context_before_provider_call():
    underlying = FakeAIProvider()
    provider = create_ai_provider(
        provider=underlying,
        redactor=FakeRedactor(),
    )

    result = provider.generate(
        "Write to alex@example.com",
        {"thread": {"body": "Contact alex@example.com"}},
    )

    assert result == "fake response"
    sent_prompt, sent_context = underlying.calls[0]
    assert "alex@example.com" not in sent_prompt
    assert (
        sent_context["thread"]["body"]
        == "Contact [REDACTED_EMAIL]"
    )


def test_factory_defaults_to_ollama_behind_privacy_boundary():
    provider = create_ai_provider()

    assert isinstance(provider, PrivacyBoundaryProvider)
    assert isinstance(provider._provider, OllamaProvider)

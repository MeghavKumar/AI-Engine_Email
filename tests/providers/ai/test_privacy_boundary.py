import pytest

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


class BrokenRedactor:
    def redact(self, text):
        raise ValueError("redaction failed")


def test_redacts_prompt_before_provider_call():
    provider = FakeAIProvider()
    boundary = PrivacyBoundaryProvider(provider, FakeRedactor())

    result = boundary.generate("Contact alex@example.com")

    assert result == "fake response"
    assert provider.calls[0][0] == "Contact [REDACTED_EMAIL]"
    assert "alex@example.com" not in provider.calls[0][0]


def test_redacts_nested_context_before_provider_call():
    provider = FakeAIProvider()
    boundary = PrivacyBoundaryProvider(provider, FakeRedactor())
    context = {"thread": [{"body": "Email alex@example.com"}], "count": 2}

    boundary.generate("Summarize this thread", context)

    sent_context = provider.calls[0][1]
    assert sent_context["thread"][0]["body"] == "Email [REDACTED_EMAIL]"
    assert sent_context["count"] == 2
    assert context["thread"][0]["body"] == "Email alex@example.com"


def test_blocks_provider_call_when_redaction_fails():
    provider = FakeAIProvider()
    boundary = PrivacyBoundaryProvider(provider, BrokenRedactor())

    with pytest.raises(RuntimeError, match="provider call blocked"):
        boundary.generate("Sensitive content")

    assert provider.calls == []

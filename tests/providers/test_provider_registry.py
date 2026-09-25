import pytest

from app.providers.email.default_registry import create_default_registry
from app.providers.email.gmail import GmailProvider
from app.providers.email.outlook import OutlookProvider
from app.providers.email.registry import EmailProviderRegistry


def test_default_registry_supports_gmail_and_outlook():
    registry = create_default_registry()

    assert registry.supports("gmail")
    assert registry.supports("GMAIL")
    assert registry.supports("outlook")
    assert registry.supports(" OUTLOOK ")
    assert registry.names() == ("gmail", "outlook")


def test_registry_creates_gmail_provider(monkeypatch):
    registry = EmailProviderRegistry()

    registry.register("gmail", GmailProvider)

    monkeypatch.setattr(
        "app.providers.email.gmail.build",
        lambda *args, **kwargs: object(),
    )

    credentials = object()

    provider = registry.create(
        "gmail",
        credentials=credentials,
    )

    assert isinstance(provider, GmailProvider)
    assert provider.credentials is credentials


def test_registry_creates_outlook_provider():
    registry = EmailProviderRegistry()

    registry.register("outlook", OutlookProvider)

    provider = registry.create(
        "outlook",
        access_token="test-token",
    )

    assert isinstance(provider, OutlookProvider)
    assert provider.access_token == "test-token"


def test_registry_rejects_unsupported_provider():
    registry = create_default_registry()

    with pytest.raises(
        ValueError,
        match="Unsupported email provider: yahoo",
    ):
        registry.create("yahoo")


def test_registry_rejects_empty_provider_name():
    registry = EmailProviderRegistry()

    with pytest.raises(
        ValueError,
        match="Provider name cannot be empty",
    ):
        registry.register("   ", GmailProvider)


def test_registry_rejects_non_callable_factory():
    registry = EmailProviderRegistry()

    with pytest.raises(
        TypeError,
        match="Provider factory must be callable",
    ):
        registry.register("gmail", None)


def test_registry_rejects_invalid_factory_result():
    registry = EmailProviderRegistry()

    registry.register("invalid", lambda: object())

    with pytest.raises(
        TypeError,
        match="did not return an EmailProvider",
    ):
        registry.create("invalid")

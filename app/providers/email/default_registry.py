from app.providers.email.gmail import GmailProvider
from app.providers.email.outlook import OutlookProvider
from app.providers.email.registry import EmailProviderRegistry


def create_default_registry() -> EmailProviderRegistry:
    """Create a registry containing the currently supported providers."""

    registry = EmailProviderRegistry()

    registry.register("gmail", GmailProvider)
    registry.register("outlook", OutlookProvider)

    return registry

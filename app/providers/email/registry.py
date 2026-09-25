from collections.abc import Callable
from typing import Any

from app.providers.email.base import EmailProvider


ProviderFactory = Callable[..., EmailProvider]


class EmailProviderRegistry:
    """Registry for constructing configured email providers."""

    def __init__(self) -> None:
        self._providers: dict[str, ProviderFactory] = {}

    def register(
        self,
        name: str,
        factory: ProviderFactory,
    ) -> None:
        """Register a provider factory under a normalized name."""

        normalized_name = name.strip().lower()

        if not normalized_name:
            raise ValueError(
                "Provider name cannot be empty."
            )

        if not callable(factory):
            raise TypeError(
                "Provider factory must be callable."
            )

        self._providers[normalized_name] = factory

    def create(
        self,
        name: str,
        **kwargs: Any,
    ) -> EmailProvider:
        """Create a registered provider using supplied dependencies."""

        normalized_name = name.strip().lower()

        if normalized_name not in self._providers:
            supported = ", ".join(
                sorted(self._providers)
            )
            raise ValueError(
                f"Unsupported email provider: {name}. "
                f"Supported providers: {supported or 'none'}."
            )

        provider = self._providers[normalized_name](**kwargs)

        if not isinstance(provider, EmailProvider):
            raise TypeError(
                f"Provider factory for '{normalized_name}' "
                "did not return an EmailProvider."
            )

        return provider

    def supports(self, name: str) -> bool:
        """Return whether a provider is registered."""

        return name.strip().lower() in self._providers

    def names(self) -> tuple[str, ...]:
        """Return registered provider names."""

        return tuple(sorted(self._providers))

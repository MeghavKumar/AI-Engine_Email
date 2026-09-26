from typing import Any

from sqlalchemy.orm import Session

from app.db.repositories.email_account import EmailAccountRepository
from app.models import EmailAccount
from app.providers.email.base import EmailProvider
from app.providers.email.default_registry import create_default_registry
from app.providers.email.registry import EmailProviderRegistry


class EmailAccountService:
    """Service for resolving and managing connected email accounts."""

    def __init__(
        self,
        session: Session,
        provider_registry: EmailProviderRegistry | None = None,
    ):
        self.repository = EmailAccountRepository(session)
        self.provider_registry = (
            provider_registry
            if provider_registry is not None
            else create_default_registry()
        )

    def get_by_id(self, account_id: int) -> EmailAccount | None:
        """Return an email account by ID."""
        return self.repository.get_by_id(account_id)

    def get_active_by_user(self, user_id: str) -> list[EmailAccount]:
        """Return all active email accounts belonging to a user."""
        return self.repository.get_active_by_user(user_id)

    def require_active(self, account_id: int) -> EmailAccount:
        """Return an active account or raise ValueError if unavailable."""
        account = self.repository.get_by_id(account_id)

        if account is None:
            raise ValueError(f"Email account {account_id} not found.")

        if not account.is_active:
            raise ValueError(f"Email account {account_id} is inactive.")

        return account

    def create_provider(
        self,
        account: EmailAccount,
        **provider_kwargs: Any,
    ) -> EmailProvider:
        """Create the provider configured for an email account."""
        if not account.is_active:
            raise ValueError(
                f"Email account {account.id} is inactive."
            )

        return self.provider_registry.create(
            account.provider,
            **provider_kwargs,
        )

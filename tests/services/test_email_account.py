import pytest

from app.db.session import SessionLocal
from app.models import EmailAccount
from app.services.email_account import EmailAccountService


def test_get_by_id():
    with SessionLocal() as session:
        account = EmailAccount(
            user_id="service-test-user-get",
            provider="gmail",
            email_address="service-get@example.com",
        )
        session.add(account)
        session.flush()

        service = EmailAccountService(session)

        loaded = service.get_by_id(account.id)

        assert loaded is not None
        assert loaded.id == account.id
        assert loaded.email_address == account.email_address

        session.delete(account)
        session.commit()


def test_get_active_by_user_returns_only_active_accounts():
    with SessionLocal() as session:
        accounts = [
            EmailAccount(
                user_id="service-test-user-active",
                provider="gmail",
                email_address="service-active@example.com",
                is_active=True,
            ),
            EmailAccount(
                user_id="service-test-user-active",
                provider="outlook",
                email_address="service-inactive@example.com",
                is_active=False,
            ),
        ]

        session.add_all(accounts)
        session.flush()

        service = EmailAccountService(session)

        loaded = service.get_active_by_user(
            "service-test-user-active"
        )

        assert len(loaded) == 1
        assert loaded[0].email_address == "service-active@example.com"

        for account in accounts:
            session.delete(account)

        session.commit()


def test_require_active_returns_active_account():
    with SessionLocal() as session:
        account = EmailAccount(
            user_id="service-test-user-required",
            provider="gmail",
            email_address="service-required@example.com",
            is_active=True,
        )
        session.add(account)
        session.flush()

        service = EmailAccountService(session)

        loaded = service.require_active(account.id)

        assert loaded.id == account.id
        assert loaded.is_active is True

        session.delete(account)
        session.commit()


def test_require_active_rejects_missing_account():
    with SessionLocal() as session:
        service = EmailAccountService(session)

        with pytest.raises(ValueError, match="not found"):
            service.require_active(999999999)


def test_require_active_rejects_inactive_account():
    with SessionLocal() as session:
        account = EmailAccount(
            user_id="service-test-user-inactive",
            provider="gmail",
            email_address="service-inactive-required@example.com",
            is_active=False,
        )
        session.add(account)
        session.flush()

        service = EmailAccountService(session)

        with pytest.raises(ValueError, match="inactive"):
            service.require_active(account.id)

        session.delete(account)
        session.commit()


def test_create_provider_resolves_gmail_account():
    from app.providers.email.base import EmailProvider
    from app.providers.email.registry import EmailProviderRegistry

    class FakeGmailProvider(EmailProvider):
        def list_messages(self, account_id: str) -> list[dict]:
            return []

        def get_message(
            self,
            account_id: str,
            message_id: str,
        ) -> dict:
            return {}

        def send_message(
            self,
            account_id: str,
            message: dict,
        ) -> str:
            return "fake-gmail-send"

        def mark_read(
            self,
            account_id: str,
            message_id: str,
        ) -> None:
            return None

        def archive_message(
            self,
            account_id: str,
            message_id: str,
        ) -> None:
            return None

        def get_thread(
            self,
            account_id: str,
            thread_id: str,
        ) -> list[dict]:
            return []

    registry = EmailProviderRegistry()
    registry.register("gmail", FakeGmailProvider)

    with SessionLocal() as session:
        account = EmailAccount(
            user_id="service-test-user-gmail",
            provider="gmail",
            email_address="service-gmail@example.com",
            is_active=True,
        )
        session.add(account)
        session.flush()

        service = EmailAccountService(
            session,
            provider_registry=registry,
        )

        provider = service.create_provider(account)

        assert isinstance(provider, FakeGmailProvider)

        session.delete(account)
        session.commit()


def test_create_provider_resolves_outlook_account():
    from app.providers.email.base import EmailProvider
    from app.providers.email.registry import EmailProviderRegistry

    class FakeOutlookProvider(EmailProvider):
        def list_messages(self, account_id: str) -> list[dict]:
            return []

        def get_message(
            self,
            account_id: str,
            message_id: str,
        ) -> dict:
            return {}

        def send_message(
            self,
            account_id: str,
            message: dict,
        ) -> str:
            return "fake-outlook-send"

        def mark_read(
            self,
            account_id: str,
            message_id: str,
        ) -> None:
            return None

        def archive_message(
            self,
            account_id: str,
            message_id: str,
        ) -> None:
            return None

        def get_thread(
            self,
            account_id: str,
            thread_id: str,
        ) -> list[dict]:
            return []

    registry = EmailProviderRegistry()
    registry.register("outlook", FakeOutlookProvider)

    with SessionLocal() as session:
        account = EmailAccount(
            user_id="service-test-user-outlook",
            provider="outlook",
            email_address="service-outlook@example.com",
            is_active=True,
        )
        session.add(account)
        session.flush()

        service = EmailAccountService(
            session,
            provider_registry=registry,
        )

        provider = service.create_provider(account)

        assert isinstance(provider, FakeOutlookProvider)

        session.delete(account)
        session.commit()


def test_create_provider_rejects_unsupported_provider():
    from app.providers.email.registry import EmailProviderRegistry

    registry = EmailProviderRegistry()

    with SessionLocal() as session:
        account = EmailAccount(
            user_id="service-test-user-unsupported",
            provider="unsupported",
            email_address="service-unsupported@example.com",
            is_active=True,
        )
        session.add(account)
        session.flush()

        service = EmailAccountService(
            session,
            provider_registry=registry,
        )

        with pytest.raises(
            ValueError,
            match="Unsupported email provider",
        ):
            service.create_provider(account)

        session.delete(account)
        session.commit()


def test_multiple_accounts_resolve_independently():
    from app.providers.email.base import EmailProvider
    from app.providers.email.registry import EmailProviderRegistry

    class FakeGmailProvider(EmailProvider):
        def list_messages(self, account_id: str) -> list[dict]:
            return []

        def get_message(
            self,
            account_id: str,
            message_id: str,
        ) -> dict:
            return {}

        def send_message(
            self,
            account_id: str,
            message: dict,
        ) -> str:
            return "fake-gmail-send"

        def mark_read(
            self,
            account_id: str,
            message_id: str,
        ) -> None:
            return None

        def archive_message(
            self,
            account_id: str,
            message_id: str,
        ) -> None:
            return None

        def get_thread(
            self,
            account_id: str,
            thread_id: str,
        ) -> list[dict]:
            return []

    class FakeOutlookProvider(EmailProvider):
        def list_messages(self, account_id: str) -> list[dict]:
            return []

        def get_message(
            self,
            account_id: str,
            message_id: str,
        ) -> dict:
            return {}

        def send_message(
            self,
            account_id: str,
            message: dict,
        ) -> str:
            return "fake-outlook-send"

        def mark_read(
            self,
            account_id: str,
            message_id: str,
        ) -> None:
            return None

        def archive_message(
            self,
            account_id: str,
            message_id: str,
        ) -> None:
            return None

        def get_thread(
            self,
            account_id: str,
            thread_id: str,
        ) -> list[dict]:
            return []

    registry = EmailProviderRegistry()
    registry.register("gmail", FakeGmailProvider)
    registry.register("outlook", FakeOutlookProvider)

    with SessionLocal() as session:
        accounts = [
            EmailAccount(
                user_id="service-test-user-multiple",
                provider="gmail",
                email_address="multiple-gmail@example.com",
                is_active=True,
            ),
            EmailAccount(
                user_id="service-test-user-multiple",
                provider="outlook",
                email_address="multiple-outlook@example.com",
                is_active=True,
            ),
        ]

        session.add_all(accounts)
        session.flush()

        service = EmailAccountService(
            session,
            provider_registry=registry,
        )

        gmail_provider = service.create_provider(accounts[0])
        outlook_provider = service.create_provider(accounts[1])

        assert isinstance(gmail_provider, FakeGmailProvider)
        assert isinstance(outlook_provider, FakeOutlookProvider)
        assert gmail_provider is not outlook_provider

        for account in accounts:
            session.delete(account)

        session.commit()

from app.db.repositories.email_account import EmailAccountRepository
from app.db.session import SessionLocal
from app.models import EmailAccount


def test_create_account():
    email_address = "repository-create@example.com"

    with SessionLocal() as session:
        repository = EmailAccountRepository(session)

        account = repository.create(
            user_id="repository-test-user-create",
            provider="gmail",
            email_address=email_address,
            provider_account_id="gmail-account-001",
        )

        try:
            session.commit()

            assert account.id is not None
            assert account.user_id == "repository-test-user-create"
            assert account.provider == "gmail"
            assert account.email_address == email_address
            assert account.provider_account_id == "gmail-account-001"
            assert account.is_active is True
        finally:
            session.delete(account)
            session.commit()


def test_get_by_id():
    email_address = "repository-get@example.com"

    with SessionLocal() as session:
        account = EmailAccount(
            user_id="repository-test-user-get",
            provider="outlook",
            email_address=email_address,
        )
        session.add(account)
        session.flush()

        repository = EmailAccountRepository(session)

        loaded = repository.get_by_id(account.id)

        assert loaded is not None
        assert loaded.id == account.id
        assert loaded.email_address == email_address

        session.delete(account)
        session.commit()


def test_list_by_user():
    email_addresses = [
        "repository-list-gmail@example.com",
        "repository-list-outlook@example.com",
        "repository-list-other@example.com",
    ]

    with SessionLocal() as session:
        accounts = [
            EmailAccount(
                user_id="repository-test-user-list",
                provider="gmail",
                email_address=email_addresses[0],
            ),
            EmailAccount(
                user_id="repository-test-user-list",
                provider="outlook",
                email_address=email_addresses[1],
            ),
            EmailAccount(
                user_id="repository-other-user",
                provider="gmail",
                email_address=email_addresses[2],
            ),
        ]

        session.add_all(accounts)
        session.flush()

        repository = EmailAccountRepository(session)

        loaded = repository.list_by_user(
            "repository-test-user-list"
        )

        assert len(loaded) == 2
        assert [account.email_address for account in loaded] == [
            email_addresses[0],
            email_addresses[1],
        ]

        for account in accounts:
            session.delete(account)

        session.commit()


def test_get_active_by_user_excludes_inactive_accounts():
    email_addresses = [
        "repository-active@example.com",
        "repository-inactive@example.com",
    ]

    with SessionLocal() as session:
        accounts = [
            EmailAccount(
                user_id="repository-test-user-active",
                provider="gmail",
                email_address=email_addresses[0],
                is_active=True,
            ),
            EmailAccount(
                user_id="repository-test-user-active",
                provider="outlook",
                email_address=email_addresses[1],
                is_active=False,
            ),
        ]

        session.add_all(accounts)
        session.flush()

        repository = EmailAccountRepository(session)

        loaded = repository.get_active_by_user(
            "repository-test-user-active"
        )

        assert len(loaded) == 1
        assert loaded[0].email_address == email_addresses[0]

        for account in accounts:
            session.delete(account)

        session.commit()


def test_deactivate_account():
    email_address = "repository-deactivate@example.com"

    with SessionLocal() as session:
        account = EmailAccount(
            user_id="repository-test-user-deactivate",
            provider="gmail",
            email_address=email_address,
            is_active=True,
        )
        session.add(account)
        session.flush()

        repository = EmailAccountRepository(session)

        result = repository.deactivate(account)

        assert result.id == account.id
        assert result.is_active is False

        session.commit()

        loaded = repository.get_by_id(account.id)

        assert loaded is not None
        assert loaded.is_active is False

        session.delete(loaded)
        session.commit()

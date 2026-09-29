from app.db.repositories.email_thread import EmailThreadRepository
from app.db.session import SessionLocal


def test_create_and_get_by_provider_id():
    with SessionLocal() as session:
        repository = EmailThreadRepository(session)

        thread = repository.create(
            account_id=1,
            provider="gmail",
            provider_thread_id="repository-gmail-thread-1",
            subject="Hello",
        )

        try:
            session.commit()

            assert thread.id is not None
            assert thread.provider == "gmail"
            assert thread.provider_thread_id == "repository-gmail-thread-1"
            assert thread.subject == "Hello"

            found = repository.get_by_provider_id(
                account_id=1,
                provider="gmail",
                provider_thread_id="repository-gmail-thread-1",
            )

            assert found is thread
        finally:
            session.delete(thread)
            session.commit()


def test_get_by_provider_id_returns_none_for_different_provider():
    with SessionLocal() as session:
        repository = EmailThreadRepository(session)

        thread = repository.create(
            account_id=1,
            provider="gmail",
            provider_thread_id="repository-same-thread-id",
            subject="Hello",
        )

        try:
            session.commit()

            found = repository.get_by_provider_id(
                account_id=1,
                provider="outlook",
                provider_thread_id="repository-same-thread-id",
            )

            assert found is None
        finally:
            session.delete(thread)
            session.commit()


def test_update_changes_subject():
    with SessionLocal() as session:
        repository = EmailThreadRepository(session)

        thread = repository.create(
            account_id=1,
            provider="gmail",
            provider_thread_id="repository-gmail-thread-2",
            subject="Old subject",
        )

        try:
            session.commit()

            updated = repository.update(
                thread,
                subject="New subject",
            )

            session.commit()

            assert updated is thread
            assert thread.subject == "New subject"
        finally:
            session.delete(thread)
            session.commit()

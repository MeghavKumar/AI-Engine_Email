from app.providers.email.normalization import NormalizedEmailProvider
from app.schemas.provider import EmailAddress, EmailMessage


class FakeNormalizedProvider(NormalizedEmailProvider):
    def get_message(
        self,
        account_id: str,
        message_id: str,
    ) -> dict:
        return {
            "id": message_id,
        }

    def normalize_message(
        self,
        account_id: str,
        raw_message: dict,
    ) -> EmailMessage:
        return EmailMessage(
            provider="fake",
            account_id=account_id,
            message_id=raw_message["id"],
            sender=EmailAddress(
                email="sender@example.com"
            ),
        )


def test_normalized_email_provider_contract():
    provider = FakeNormalizedProvider()

    raw_message = provider.get_message(
        account_id="account-1",
        message_id="message-1",
    )

    normalized = provider.normalize_message(
        account_id="account-1",
        raw_message=raw_message,
    )

    assert raw_message == {"id": "message-1"}
    assert isinstance(normalized, EmailMessage)
    assert normalized.message_id == "message-1"


def test_normalized_email_provider_remains_abstract():
    class IncompleteProvider(NormalizedEmailProvider):
        def get_message(
            self,
            account_id: str,
            message_id: str,
        ) -> dict:
            return {}

    try:
        IncompleteProvider()
    except TypeError:
        pass
    else:
        raise AssertionError(
            "NormalizedEmailProvider should remain abstract."
        )

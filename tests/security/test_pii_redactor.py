import pytest

from app.security.pii_redactor import PiiRedactor


@pytest.fixture
def redactor():
    return PiiRedactor()


def test_redacts_email_address(redactor):
    text = "Please contact alex.smith@example.com for details."

    result = redactor.redact(text)

    assert result == "Please contact [REDACTED_EMAIL] for details."
    assert "alex.smith@example.com" not in result


def test_redacts_social_security_number(redactor):
    text = "The SSN is 123-45-6789."

    result = redactor.redact(text)

    assert result == "The SSN is [REDACTED_SSN]."
    assert "123-45-6789" not in result


@pytest.mark.parametrize(
    "phone",
    [
        "201-555-0123",
        "(201) 555-0123",
        "201.555.0123",
        "+1 201-555-0123",
    ],
)
def test_redacts_common_us_phone_formats(redactor, phone):
    result = redactor.redact(f"Call me at {phone}.")

    assert result == "Call me at [REDACTED_PHONE]."
    assert phone not in result


@pytest.mark.parametrize(
    "phone",
    [
        "+44 20 7946 0958",
        "+33 6 12 34 56 78",
        "+91 98765 43210",
        "+81 90-1234-5678",
    ],
)
def test_redacts_international_phone_formats(redactor, phone):
    result = redactor.redact(f"Call me at {phone}.")

    assert phone not in result
    assert "[REDACTED_PHONE]" in result


def test_redacts_iban(redactor):
    text = "Please transfer funds to GB82 WEST 1234 5698 7654 32."

    result = redactor.redact(text)

    assert "GB82 WEST 1234 5698 7654 32" not in result
    assert "[REDACTED_IBAN]" in result


def test_redacts_credit_card_number(redactor):
    text = "The card number is 4111 1111 1111 1111."

    result = redactor.redact(text)

    assert "4111 1111 1111 1111" not in result
    assert "[REDACTED_CREDIT_CARD]" in result


def test_redacts_multiple_pii_patterns(redactor):
    text = (
        "Email alex@example.com, call (201) 555-0123, "
        "and verify SSN 123-45-6789."
    )

    result = redactor.redact(text)

    assert "[REDACTED_EMAIL]" in result
    assert "[REDACTED_PHONE]" in result
    assert "[REDACTED_SSN]" in result
    assert "alex@example.com" not in result
    assert "(201) 555-0123" not in result
    assert "123-45-6789" not in result


def test_leaves_ordinary_text_unchanged(redactor):
    text = "Please review the project update before Friday."

    assert redactor.redact(text) == text


def test_rejects_non_string_input(redactor):
    with pytest.raises(TypeError, match="text must be a string"):
        redactor.redact(None)

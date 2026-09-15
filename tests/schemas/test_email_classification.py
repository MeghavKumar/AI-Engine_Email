import pytest
from pydantic import ValidationError

from app.schemas.email import (
    EmailCategory,
    EmailClassification,
    EmailPriority,
)


def test_valid_email_classification():
    classification = EmailClassification(
        category=EmailCategory.ACTION_REQUIRED,
        priority=EmailPriority.HIGH,
        requires_action=True,
        confidence=0.95,
    )

    assert classification.category == EmailCategory.ACTION_REQUIRED
    assert classification.priority == EmailPriority.HIGH
    assert classification.requires_action is True
    assert classification.confidence == 0.95


def test_invalid_category_is_rejected():
    with pytest.raises(ValidationError):
        EmailClassification(
            category="INVALID_CATEGORY",
            priority="HIGH",
            requires_action=True,
            confidence=0.95,
        )


def test_invalid_priority_is_rejected():
    with pytest.raises(ValidationError):
        EmailClassification(
            category="ACTION_REQUIRED",
            priority="INVALID_PRIORITY",
            requires_action=True,
            confidence=0.95,
        )


def test_confidence_must_be_between_zero_and_one():
    with pytest.raises(ValidationError):
        EmailClassification(
            category="INFORMATIONAL",
            priority="LOW",
            requires_action=False,
            confidence=1.5,
        )

from app.schemas.email import (
    EmailCategory,
    EmailClassification,
    EmailPriority,
    TriageAction,
)
from app.services.triage import EmailTriageService


def make_classification(
    category: EmailCategory,
    priority: EmailPriority = EmailPriority.LOW,
    requires_action: bool = False,
) -> EmailClassification:
    return EmailClassification(
        category=category,
        priority=priority,
        requires_action=requires_action,
        confidence=0.95,
    )


def test_spam_is_recommended_for_archive():
    service = EmailTriageService()

    result = service.decide(
        make_classification(EmailCategory.SPAM)
    )

    assert result.action == TriageAction.ARCHIVE
    assert "SPAM" in result.reason


def test_promotion_is_recommended_for_archive():
    service = EmailTriageService()

    result = service.decide(
        make_classification(EmailCategory.PROMOTION)
    )

    assert result.action == TriageAction.ARCHIVE
    assert "PROMOTION" in result.reason


def test_action_required_is_sent_for_review():
    service = EmailTriageService()

    result = service.decide(
        make_classification(
            EmailCategory.ACTION_REQUIRED,
            priority=EmailPriority.HIGH,
            requires_action=True,
        )
    )

    assert result.action == TriageAction.REVIEW


def test_informational_email_requires_no_action():
    service = EmailTriageService()

    result = service.decide(
        make_classification(EmailCategory.INFORMATIONAL)
    )

    assert result.action == TriageAction.NO_ACTION


def test_requires_action_overrides_informational_category():
    service = EmailTriageService()

    result = service.decide(
        make_classification(
            EmailCategory.INFORMATIONAL,
            priority=EmailPriority.HIGH,
            requires_action=True,
        )
    )

    assert result.action == TriageAction.REVIEW

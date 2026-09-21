from app.schemas.reminder import ReminderDraft
from app.schemas.email import SecurityAssessment
from app.services.reminder_security import ReminderSecurityService


class FakeSecurityGateway:
    def __init__(self, assessment: SecurityAssessment):
        self.assessment = assessment
        self.inspected_text = None

    def inspect_text(self, text: str) -> SecurityAssessment:
        self.inspected_text = text
        return self.assessment


def make_reminder() -> ReminderDraft:
    return ReminderDraft(
        to=["recipient@example.com"],
        subject="Follow-up",
        body="Just following up on my previous email.",
    )


def test_safe_reminder_passes_security_check():
    assessment = SecurityAssessment(
        safe=True,
        pii_detected=False,
        prompt_injection_detected=False,
        reasons=[],
    )
    gateway = FakeSecurityGateway(assessment)
    service = ReminderSecurityService(gateway)

    result = service.inspect(make_reminder())

    assert result.safe is True
    assert result.pii_detected is False
    assert result.prompt_injection_detected is False


def test_security_gateway_receives_subject_and_body():
    assessment = SecurityAssessment(
        safe=True,
        pii_detected=False,
        prompt_injection_detected=False,
        reasons=[],
    )
    gateway = FakeSecurityGateway(assessment)
    service = ReminderSecurityService(gateway)

    service.inspect(make_reminder())

    assert gateway.inspected_text == (
        "Follow-up\n\nJust following up on my previous email."
    )


def test_unsafe_reminder_result_is_preserved():
    assessment = SecurityAssessment(
        safe=False,
        pii_detected=True,
        prompt_injection_detected=False,
        reasons=["Sensitive information detected."],
    )
    gateway = FakeSecurityGateway(assessment)
    service = ReminderSecurityService(gateway)

    result = service.inspect(make_reminder())

    assert result.safe is False
    assert result.pii_detected is True
    assert result.reasons == ["Sensitive information detected."]

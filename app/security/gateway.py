from app.schemas.email import SecurityAssessment


class SecurityGateway:
    """
    Shared security boundary for inbound and outbound
    AI email workflows.

    Future responsibilities:
    - PII detection
    - selective redaction/tokenization
    - prompt-injection detection
    - attachment safety checks
    - outbound policy checks
    """

    def inspect_text(
        self,
        text: str,
    ) -> SecurityAssessment:

        # Initial implementation.
        # Real security controls will be added before
        # production email sending is enabled.

        return SecurityAssessment(
            safe=True,
            pii_detected=False,
            prompt_injection_detected=False,
            reasons=[],
        )

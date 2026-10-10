import re

from app.schemas.email import SecurityAssessment
from app.security.pii_redactor import PiiRedactor


class SecurityGateway:
    """Conservative security checks before content enters an AI workflow."""

    _PROMPT_INJECTION_PATTERNS = (
        re.compile(
            r"\b(ignore|disregard|override|forget)\b.{0,60}"
            r"\b(previous|prior|all|above|earlier)\b.{0,30}"
            r"\b(instructions?|rules?|prompts?)\b",
            re.IGNORECASE,
        ),
        re.compile(
            r"\b(reveal|show|print|disclose|expose)\b.{0,50}"
            r"\b(system prompt|developer message|hidden instructions?)\b",
            re.IGNORECASE,
        ),
        re.compile(
            r"\b(send|share|reveal|exfiltrate|disclose)\b.{0,50}"
            r"\b(all credentials|passwords|access tokens|secrets)\b",
            re.IGNORECASE,
        ),
    )

    def __init__(self, redactor=None) -> None:
        self._redactor = redactor if redactor is not None else PiiRedactor()

    def inspect_text(self, text: str) -> SecurityAssessment:
        """Assess text and fail closed if the PII check cannot complete."""

        try:
            redacted_text = self._redactor.redact(text)
        except Exception:
            # Do not expose exception details; they may contain sensitive data.
            return SecurityAssessment(
                safe=False,
                pii_detected=False,
                prompt_injection_detected=False,
                reasons=["PII analysis failed; content blocked."],
            )

        pii_detected = redacted_text != text
        prompt_injection_detected = any(
            pattern.search(text)
            for pattern in self._PROMPT_INJECTION_PATTERNS
        )

        reasons = []
        if pii_detected:
            reasons.append("Potential PII detected; content requires redaction.")
        if prompt_injection_detected:
            reasons.append("Potential prompt-injection language detected.")

        return SecurityAssessment(
            safe=not pii_detected and not prompt_injection_detected,
            pii_detected=pii_detected,
            prompt_injection_detected=prompt_injection_detected,
            reasons=reasons,
        )

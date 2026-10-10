import re

from presidio_analyzer import AnalyzerEngine, RecognizerResult

from app.schemas.email import SecurityAssessment
from app.security.redaction_result import RedactionResult

from app.schemas.email import SecurityAssessment
from app.security.redaction_result import RedactionResult


class PiiRedactor:
    """
    Redact recognized PII using Presidio.

    NLP-based name and location detection currently uses English.
    Detection is not guaranteed to identify every sensitive value.
    """

    _ENTITY_LABELS = {
        "EMAIL_ADDRESS": "EMAIL",
        "PHONE_NUMBER": "PHONE",
        "US_SSN": "SSN",
        "IBAN_CODE": "IBAN",
        "CREDIT_CARD": "CREDIT_CARD",
        "PERSON": "PERSON",
        "LOCATION": "LOCATION",
        "US_BANK_NUMBER": "BANK_NUMBER",
        "US_ITIN": "ITIN",
        "US_DRIVER_LICENSE": "DRIVER_LICENSE",
        "US_PASSPORT": "PASSPORT",
        "UK_NHS": "NHS_ID",
        "IP_ADDRESS": "IP_ADDRESS",
    }

    _SSN_PATTERN = re.compile(r"(?<!\d)\d{3}-\d{2}-\d{4}(?!\d)")

    def __init__(self, analyzer: AnalyzerEngine | None = None) -> None:
        # Allow an injected analyzer in tests and alternative deployments.
        self._analyzer = (
            analyzer if analyzer is not None else AnalyzerEngine()
        )

    def redact(self, text: str) -> str:
        """Preserve the existing API, returning only sanitized text."""
        return self.redact_with_result(text).redacted_text

    def redact_with_result(self, text: str) -> RedactionResult:
        """Return sanitized text and a local-only replacement map."""
        if not isinstance(text, str):
            raise TypeError("text must be a string")

        if not text:
            return RedactionResult(
                redacted_text=text,
                assessment=SecurityAssessment(safe=True),
            )

        findings = self._analyzer.analyze(
            text=text,
            language="en",
            entities=list(self._ENTITY_LABELS),
        )

        for match in self._SSN_PATTERN.finditer(text):
            if not any(
                finding.entity_type == "US_SSN"
                and finding.start == match.start()
                and finding.end == match.end()
                for finding in findings
            ):
                findings.append(
                    RecognizerResult(
                        entity_type="US_SSN",
                        start=match.start(),
                        end=match.end(),
                        score=1.0,
                    )
                )

        findings = sorted(
            findings,
            key=lambda item: (item.start, -(item.end - item.start)),
        )

        selected = []
        cursor = 0

        for finding in findings:
            if finding.start < cursor:
                continue

            label = self._ENTITY_LABELS.get(finding.entity_type)
            if label is None:
                continue

            selected.append((finding.start, finding.end, label))
            cursor = finding.end

        redacted = text
        replacements: dict[str, str] = {}

        for start, end, label in reversed(selected):
            token = f"[REDACTED_{label}]"
            replacements.setdefault(token, text[start:end])
            redacted = redacted[:start] + token + redacted[end:]

        return RedactionResult(
            redacted_text=redacted,
            assessment=SecurityAssessment(
                safe=not selected,
                pii_detected=bool(selected),
                reasons=(
                    ["Potential PII detected and redacted."]
                    if selected
                    else []
                ),
            ),
            replacements=replacements,
        )

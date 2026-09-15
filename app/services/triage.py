from app.schemas.email import (
    EmailCategory,
    EmailClassification,
    TriageAction,
    TriageDecision,
)


class EmailTriageService:
    """Convert an email classification into a safe recommended action."""

    def decide(
        self,
        classification: EmailClassification,
    ) -> TriageDecision:
        if classification.category in {
            EmailCategory.SPAM,
            EmailCategory.PROMOTION,
        }:
            return TriageDecision(
                action=TriageAction.ARCHIVE,
                reason=(
                    f"Email classified as "
                    f"{classification.category.value}."
                ),
            )

        if classification.category == EmailCategory.ACTION_REQUIRED:
            return TriageDecision(
                action=TriageAction.REVIEW,
                reason="Email requires user action.",
            )

        return TriageDecision(
            action=TriageAction.NO_ACTION,
            reason="Informational email does not require action.",
        )

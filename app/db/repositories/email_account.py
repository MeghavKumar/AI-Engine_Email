from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.email_account import EmailAccount


class EmailAccountRepository:
    """Database repository for connected email accounts."""

    def __init__(self, session: Session):
        self.session = session

    def create(
        self,
        user_id: str,
        provider: str,
        email_address: str,
        provider_account_id: str | None = None,
        is_active: bool = True,
    ) -> EmailAccount:
        account = EmailAccount(
            user_id=user_id,
            provider=provider,
            email_address=email_address,
            provider_account_id=provider_account_id,
            is_active=is_active,
        )

        self.session.add(account)
        self.session.flush()

        return account

    def get_by_id(
        self,
        account_id: int,
    ) -> EmailAccount | None:
        statement = select(EmailAccount).where(
            EmailAccount.id == account_id
        )

        return self.session.scalar(statement)

    def list_by_user(
        self,
        user_id: str,
    ) -> list[EmailAccount]:
        statement = (
            select(EmailAccount)
            .where(EmailAccount.user_id == user_id)
            .order_by(EmailAccount.id)
        )

        return list(self.session.scalars(statement))

    def get_active_by_user(
        self,
        user_id: str,
    ) -> list[EmailAccount]:
        statement = (
            select(EmailAccount)
            .where(
                EmailAccount.user_id == user_id,
                EmailAccount.is_active.is_(True),
            )
            .order_by(EmailAccount.id)
        )

        return list(self.session.scalars(statement))

    def deactivate(
        self,
        account: EmailAccount,
    ) -> EmailAccount:
        account.is_active = False
        self.session.flush()

        return account

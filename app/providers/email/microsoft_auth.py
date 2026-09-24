from dataclasses import dataclass

import msal


@dataclass(frozen=True)
class MicrosoftAuthConfig:
    """Configuration for Microsoft identity authentication.

    This configuration is intentionally provider-agnostic and does not
    perform authentication itself. Live Microsoft authentication can be
    added later when tenant authorization is available.
    """

    client_id: str
    tenant: str = "common"
    scopes: tuple[str, ...] = (
        "Mail.Read",
        "Mail.Send",
    )


class MicrosoftAuth:
    """Microsoft OAuth authentication service.

    Live authentication is intentionally not invoked during development.
    """

    def __init__(self, config: MicrosoftAuthConfig):
        self.config = config
        self.client = msal.PublicClientApplication(
            client_id=config.client_id,
            authority=f"https://login.microsoftonline.com/{config.tenant}",
        )


    def get_cached_account(self):
        """Return the first cached account, if one exists.

        This method only inspects MSAL's local in-memory cache.
        It does not contact Microsoft.
        """
        accounts = self.client.get_accounts()
        return accounts[0] if accounts else None

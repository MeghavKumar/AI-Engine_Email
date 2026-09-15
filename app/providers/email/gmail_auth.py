from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow


class GmailAuth:
    """Handle local Gmail OAuth authentication."""

    SCOPES = [
        "https://www.googleapis.com/auth/gmail.readonly",
    ]

    def __init__(
        self,
        credentials_file: str = "credentials.json",
        token_file: str = "gmail_token.json",
    ):
        self.credentials_file = Path(credentials_file)
        self.token_file = Path(token_file)

    def authenticate(self) -> Credentials:
        credentials = None

        if self.token_file.exists():
            credentials = Credentials.from_authorized_user_file(
                self.token_file,
                self.SCOPES,
            )

        if credentials and credentials.valid:
            return credentials

        if (
            credentials
            and credentials.expired
            and credentials.refresh_token
        ):
            credentials.refresh(Request())
        else:
            if not self.credentials_file.exists():
                raise FileNotFoundError(
                    f"Google OAuth credentials not found: "
                    f"{self.credentials_file}"
                )

            flow = InstalledAppFlow.from_client_secrets_file(
                self.credentials_file,
                self.SCOPES,
            )

            credentials = flow.run_local_server(port=0)

        self.token_file.write_text(credentials.to_json())

        return credentials

"""Google OAuth authentication and Gmail/Calendar API clients."""

import logging
import os
from functools import lru_cache
from pathlib import Path

from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)

CREDENTIALS_FILE = Path(
    os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials(2).json")
)

TOKEN_FILE = Path(
    os.getenv("GOOGLE_TOKEN_FILE", "token.json")
)

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.compose",
    "https://www.googleapis.com/auth/calendar.events",
]


def _save_credentials(credentials: Credentials) -> None:
    """Persist Google credentials securely."""
    TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)

    TOKEN_FILE.write_text(
        credentials.to_json(),
        encoding="utf-8",
    )

    try:
        TOKEN_FILE.chmod(0o600)
    except OSError:
        logger.debug("Could not restrict token file permissions.")


def get_credentials_without_login() -> Credentials | None:
    """
    Load and refresh Google credentials without opening a browser.

    Returns None if authentication is missing or cannot be refreshed.
    """
    if not TOKEN_FILE.exists():
        return None

    try:
        credentials = Credentials.from_authorized_user_file(
            str(TOKEN_FILE),
            SCOPES,
        )
    except Exception:
        logger.warning("Could not load Google token file.")
        return None

    if credentials and credentials.expired and credentials.refresh_token:
        try:
            credentials.refresh(Request())
            _save_credentials(credentials)
        except RefreshError:
            logger.warning(
                "Google refresh token is invalid or expired; "
                "manual reauthorization is required."
            )
            return None

    if credentials and credentials.valid:
        return credentials

    return None


def get_credentials() -> Credentials:
    """
    Load valid Google credentials or start local OAuth consent.

    This may open a browser, so call it only from Gmail/Calendar tools,
    not from a connection-status MCP tool.
    """
    credentials = get_credentials_without_login()

    if credentials:
        return credentials

    if not CREDENTIALS_FILE.exists():
        raise FileNotFoundError(
            f"Google OAuth credentials file not found: "
            f"{CREDENTIALS_FILE.resolve()}"
        )

    flow = InstalledAppFlow.from_client_secrets_file(
        str(CREDENTIALS_FILE),
        SCOPES,
    )

    credentials = flow.run_local_server(port=0)
    _save_credentials(credentials)

    return credentials


@lru_cache(maxsize=1)
def _get_credentials_cached() -> Credentials:
    """Cache credentials for repeated MCP tool calls."""
    return get_credentials()


def get_gmail_service():
    """Build an authenticated Gmail API client."""
    return build(
        "gmail",
        "v1",
        credentials=_get_credentials_cached(),
        cache_discovery=False,
    )


def get_calendar_service():
    """Build an authenticated Google Calendar API client."""
    return build(
        "calendar",
        "v3",
        credentials=_get_credentials_cached(),
        cache_discovery=False,
    )


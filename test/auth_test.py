from backend.src.mcp.google_auth import (
    get_credentials_without_login,
    get_gmail_service,
    get_calendar_service,
)


def test_google_connection():
    credentials = get_credentials_without_login()

    assert credentials is not None, (
        "Google credentials are not available. "
        "Run scripts/google_login.py first."
    )

    gmail = get_gmail_service()
    calendar = get_calendar_service()

    assert gmail is not None
    assert calendar is not None

    print("Google connection test passed.")
    print("Gmail and Calendar API clients created successfully.")


if __name__ == "__main__":
    test_google_connection()
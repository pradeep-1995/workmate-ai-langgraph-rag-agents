"""Local MCP server exposing Gmail and Google Calendar API tools."""

# Built-in modules

# Purpose : Converts binary data into a text representation.
import base64
# Purpose : Records information about what your application is doing.
import logging
# Purpose : Provides access to Python interpreter information and certain runtime functions.
import sys


# date : Represents a calendar date (October 26)
# datetime : Represents a date and time (October 26,AM)
# time : Represents a time of day (10:30 AM)
# timedelta : Represents a duration (2 hr)
from datetime import date, datetime, time, timedelta
# Purpose : Creates an email message containing text, including plain text or HTML
from email.mime.text import MIMEText
# Purpose : Helps you describe the types of values your Python code can accepts or return.
from typing import Any
# Purpose : Handles time zones.
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

# Purpose : Parses HTML and helps extract information from web pages.
from bs4 import BeautifulSoup
# Handles HTTP errors returned by Google API requests made through the Google API Python client.
from googleapiclient.errors import HttpError


from fastmcp import FastMCP

from backend.core.google_auth import (
    get_credentials,
    get_credentials_without_login,
    get_gmail_service,
    get_calendar_service,
)

logger = logging.getLogger(__name__)

mcp = FastMCP("Google_Workspace")


# ============================================================
# HELPERS
# ============================================================

def _error_response(operation: str, exc: Exception) -> dict:

    """Log technical details without exposing them to the agent."""
    logger.exception("%s failed", operation)

    if isinstance(exc, HttpError):
        status = getattr(exc.resp, "status", None)

        if status == 401:
            message = "Google authentication failed. Reconnect your account."
        elif status == 403:
            message = "Google denied access. Check API permissions and OAuth scopes."
        elif status == 404:
            message = "The requested Google resource was not found."
        elif status == 429:
            message = "Google API rate limit reached. Try again later."
        else:
            message = "Google API request failed."
    else:
        message = "The operation failed. Check the server logs."

    return {
        "success": False,
        "error": message,
    }


def _decode_message_body(payload: dict[str, Any]) -> str:
    """Find and decode a readable email body recursively."""

    if payload.get("mimeType") == "text/plain":
        data = payload.get("body", {}).get("data")

        if data:
            decoded = base64.urlsafe_b64decode(
                data + "=" * (-len(data) % 4)
            )
            return decoded.decode("utf-8", errors="replace")

    for part in payload.get("parts", []):
        body = _decode_message_body(part)

        if body:
            return body

    if payload.get("mimeType") == "text/html":
        data = payload.get("body", {}).get("data")

        if data:
            decoded = base64.urlsafe_b64decode(
                data + "=" * (-len(data) % 4)
            ).decode("utf-8", errors="replace")

            soup = BeautifulSoup(decoded, "html.parser")
            return soup.get_text(separator="\n").strip()

    return ""


def _message_headers(payload: dict[str, Any]) -> dict[str, str]:
    """Extract useful email headers safely."""
    headers = payload.get("headers", [])

    return {
        header.get("name", "").lower(): header.get("value", "")
        for header in headers
    }


def _parse_date(value: str) -> date:
    """Validate and parse a YYYY-MM-DD date."""
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        raise ValueError("Dates must use YYYY-MM-DD format.") from None


def _validate_timezone(timezone: str) -> ZoneInfo:
    """Return a valid IANA time zone."""
    try:
        return ZoneInfo(timezone)
    except (ZoneInfoNotFoundError, ValueError):
        raise ValueError("Invalid time zone.") from None


def _build_email_raw(to: str, subject: str, body: str) -> str:
    """Create a base64url-encoded Gmail message."""
    message = MIMEText(body, "plain", "utf-8")
    message["To"] = to
    message["Subject"] = subject

    return base64.urlsafe_b64encode(
        message.as_bytes()
    ).decode("ascii")


# ============================================================
# ACCOUNT STATUS
# ============================================================

@mcp.tool()
def get_google_account_status() -> dict:
    """Check whether Google credentials are available without login."""
    credentials = get_credentials_without_login()

    if credentials is None:
        return {
            "success": True,
            "connected": False,
            "message": (
                "Google is not connected. Run the OAuth login script "
                "outside the MCP server to authenticate."
            ),
        }

    return {
        "success": True,
        "connected": True,
        "message": "Google credentials are available.",
    }


# ============================================================
# GMAIL TOOLS
# ============================================================

@mcp.tool()
def search_emails(
    query: str,
    max_results: int = 5,
) -> dict:
    """Search Gmail using Gmail search syntax.

    Examples:
    - from:recruiter@example.com
    - subject:interview
    - is:unread

    Returns message IDs, sender, subject, date, and snippet.
    """
    query = query.strip()

    if not query:
        return {
            "success": False,
            "error": "Search query cannot be empty.",
        }

    if not 1 <= max_results <= 50:
        return {
            "success": False,
            "error": "max_results must be between 1 and 50.",
        }

    try:
        service = get_gmail_service()

        response = (
            service.users()
            .messages()
            .list(
                userId="me",
                q=query,
                maxResults=max_results,
            )
            .execute()
        )

        results = []

        for item in response.get("messages", []):
            detail = (
                service.users()
                .messages()
                .get(
                    userId="me",
                    id=item["id"],
                    format="metadata",
                    metadataHeaders=["From", "To", "Subject", "Date"],
                )
                .execute()
            )

            headers = _message_headers(detail.get("payload", {}))

            results.append(
                {
                    "id": detail.get("id", ""),
                    "thread_id": detail.get("threadId", ""),
                    "from": headers.get("from", ""),
                    "to": headers.get("to", ""),
                    "subject": headers.get("subject", ""),
                    "date": headers.get("date", ""),
                    "snippet": detail.get("snippet", ""),
                }
            )

        return {
            "success": True,
            "count": len(results),
            "messages": results,
            "next_page_token": response.get("nextPageToken"),
        }

    except Exception as exc:
        return _error_response("Gmail search", exc)



@mcp.tool()
def read_email(message_id: str) -> dict:
    """Read the text content and metadata of a Gmail message.

    Supply the message ID returned by search_emails.
    """
    message_id = message_id.strip()

    if not message_id:
        return {
            "success": False,
            "error": "Message ID cannot be empty.",
        }

    try:
        service = get_gmail_service()

        message = (
            service.users()
            .messages()
            .get(
                userId="me",
                id=message_id,
                format="full",
            )
            .execute()
        )

        payload = message.get("payload", {})
        headers = _message_headers(payload)
        body = _decode_message_body(payload)

        return {
            "success": True,
            "id": message.get("id", ""),
            "thread_id": message.get("threadId", ""),
            "from": headers.get("from", ""),
            "to": headers.get("to", ""),
            "subject": headers.get("subject", ""),
            "date": headers.get("date", ""),
            "body": body or message.get("snippet", ""),
            "snippet": message.get("snippet", ""),
        }

    except Exception as exc:
        return _error_response("Read Gmail message", exc)



@mcp.tool()
def create_email_draft(
    to: str,
    subject: str,
    body: str,
) -> dict:
    """Create an unsent Gmail draft for the user to review."""
    to = to.strip()
    subject = subject.strip()

    if not to or not subject or not body.strip():
        return {
            "success": False,
            "error": "Recipient, subject, and body are required.",
        }

    try:
        service = get_gmail_service()

        raw_message = _build_email_raw(to, subject, body)

        draft = (
            service.users()
            .drafts()
            .create(
                userId="me",
                body={
                    "message": {
                        "raw": raw_message,
                    }
                },
            )
            .execute()
        )

        return {
            "success": True,
            "draft_id": draft.get("id"),
            "message": "Draft created. Review it in Gmail before sending.",
        }

    except Exception as exc:
        return _error_response("Create Gmail draft", exc)



@mcp.tool()
def send_email(
    to: str,
    subject: str,
    body: str,
    confirm: bool = False,
) -> dict:
    """Send an email only after the user explicitly confirms.

    Before retrying with confirm=True, show the recipient, subject,
    and full message body to the user and obtain approval.
    """
    to = to.strip()
    subject = subject.strip()

    if not to or not subject or not body.strip():
        return {
            "success": False,
            "error": "Recipient, subject, and body are required.",
        }

    if not confirm:
        return {
            "success": False,
            "confirmation_required": True,
            "recipient": to,
            "subject": subject,
            "body": body,
            "message": (
                "Show the recipient, subject, and body to the user. "
                "Send only after explicit approval."
            ),
        }

    try:
        service = get_gmail_service()

        raw_message = _build_email_raw(to, subject, body)

        sent = (
            service.users()
            .messages()
            .send(
                userId="me",
                body={"raw": raw_message},
            )
            .execute()
        )

        return {
            "success": True,
            "message_id": sent.get("id"),
            "thread_id": sent.get("threadId"),
            "message": "Email sent successfully.",
        }

    except Exception as exc:
        return _error_response("Send Gmail message", exc)


# ============================================================
# CALENDAR TOOLS
# ============================================================


@mcp.tool()
def list_calendar_events(
    start_date: str,
    end_date: str,
    max_results: int = 20,
    timezone: str = "Asia/Kolkata",
) -> dict:
    """List events between two inclusive local dates.

    Dates must use YYYY-MM-DD.
    Time zone must be a valid IANA time zone.
    """
    if not 1 <= max_results <= 250:
        return {
            "success": False,
            "error": "max_results must be between 1 and 250.",
        }

    try:
        start_day = _parse_date(start_date)
        end_day = _parse_date(end_date)
        tz = _validate_timezone(timezone)

        if end_day < start_day:
            return {
                "success": False,
                "error": "end_date must be on or after start_date.",
            }

        time_min = datetime.combine(
            start_day,
            time.min,
            tzinfo=tz,
        )

        time_max = datetime.combine(
            end_day + timedelta(days=1),
            time.min,
            tzinfo=tz,
        )

        service = get_calendar_service()

        response = (
            service.events()
            .list(
                calendarId="primary",
                timeMin=time_min.isoformat(),
                timeMax=time_max.isoformat(),
                timeZone=timezone,
                maxResults=max_results,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )

        events = []

        for event in response.get("items", []):
            events.append(
                {
                    "id": event.get("id", ""),
                    "summary": event.get("summary", "(No title)"),
                    "start": event.get("start", {}),
                    "end": event.get("end", {}),
                    "location": event.get("location", ""),
                    "description": event.get("description", ""),
                    "html_link": event.get("htmlLink", ""),
                    "status": event.get("status", ""),
                }
            )

        return {
            "success": True,
            "count": len(events),
            "events": events,
            "next_page_token": response.get("nextPageToken"),
            "timezone": timezone,
        }

    except ValueError as exc:
        return {
            "success": False,
            "error": str(exc),
        }

    except Exception as exc:
        return _error_response("List Calendar events", exc)



@mcp.tool()
def create_calendar_event(
    title: str,
    start_time: str,
    end_time: str,
    description: str = "",
    location: str = "",
    timezone: str = "Asia/Kolkata",
    confirm: bool = False,
) -> dict:
    """Create a Calendar event after user confirmation.

    start_time and end_time use YYYY-MM-DDTHH:MM:SS.
    For example: 2026-10-26T15:00:00

    Naive date-times are interpreted in the specified time zone.
    Show the event details to the user before calling with confirm=True.
    """
    title = title.strip()

    if not title:
        return {
            "success": False,
            "error": "Event title cannot be empty.",
        }

    try:
        tz = _validate_timezone(timezone)

        start = datetime.fromisoformat(start_time)
        end = datetime.fromisoformat(end_time)

        if start.tzinfo is None:
            start = start.replace(tzinfo=tz)

        if end.tzinfo is None:
            end = end.replace(tzinfo=tz)

        if end <= start:
            return {
                "success": False,
                "error": "end_time must be later than start_time.",
            }

        event_preview = {
            "title": title,
            "start": start.isoformat(),
            "end": end.isoformat(),
            "timezone": timezone,
            "description": description,
            "location": location,
        }

        if not confirm:
            return {
                "success": False,
                "confirmation_required": True,
                "event": event_preview,
                "message": (
                    "Show the event details to the user. "
                    "Create it only after explicit approval."
                ),
            }

        service = get_calendar_service()

        event_body = {
            "summary": title,
            "description": description,
            "location": location,
            "start": {
                "dateTime": start.isoformat(),
                "timeZone": timezone,
            },
            "end": {
                "dateTime": end.isoformat(),
                "timeZone": timezone,
            },
        }

        created = (
            service.events()
            .insert(
                calendarId="primary",
                body=event_body,
            )
            .execute()
        )

        return {
            "success": True,
            "event_id": created.get("id"),
            "html_link": created.get("htmlLink", ""),
            "message": "Calendar event created successfully.",
        }

    except ValueError:
        return {
            "success": False,
            "error": (
                "Invalid date-time. Use YYYY-MM-DDTHH:MM:SS "
                "and a valid IANA time zone."
            ),
        }

    except Exception as exc:
        return _error_response("Create Calendar event", exc)

@mcp.tool()
def update_calendar_event(
    event_id: str,
    title: str = "",
    start_time: str = "",
    end_time: str = "",
    description: str = "",
    location: str = "",
    timezone: str = "Asia/Kolkata",
    confirm: bool = False,
) -> dict:
    """Update a Calendar event after user confirmation.

    Provide the event ID and any fields to update.
    Show the proposed changes to the user before calling with confirm=True.
    """
    event_id = event_id.strip()

    if not event_id:
        return {
            "success": False,
            "error": "Event ID cannot be empty.",
        }

    try:
        tz = _validate_timezone(timezone)

        updates = {}

        if title.strip():
            updates["summary"] = title.strip()

        if start_time.strip():
            start = datetime.fromisoformat(start_time)
            if start.tzinfo is None:
                start = start.replace(tzinfo=tz)
            updates["start"] = {
                "dateTime": start.isoformat(),
                "timeZone": timezone,
            }

        if end_time.strip():
            end = datetime.fromisoformat(end_time)
            if end.tzinfo is None:
                end = end.replace(tzinfo=tz)
            updates["end"] = {
                "dateTime": end.isoformat(),
                "timeZone": timezone,
            }

        if description.strip():
            updates["description"] = description.strip()

        if location.strip():
            updates["location"] = location.strip()

        if not updates:
            return {
                "success": False,
                "error": "No fields provided to update.",
            }

        if not confirm:
            return {
                "success": False,
                "confirmation_required": True,
                "proposed_updates": updates,
                "message": (
                    "Show the proposed changes to the user. "
                    "Update only after explicit approval."
                ),
            }

        service = get_calendar_service()

        updated_event = (
            service.events()
            .patch(
                calendarId="primary",
                eventId=event_id,
                body=updates,
            )
            .execute()
        )

        return {
            "success": True,
            "event_id": updated_event.get("id"),
            "html_link": updated_event.get("htmlLink", ""),
            "message": "Calendar event updated successfully.",
        }

    except ValueError:
        return {
            "success": False,
            "error": "Invalid date/time format.",
        }

@mcp.tool()
def delete_calendar_event(
    event_id: str,
    confirm: bool = False,
) -> dict:
    """Delete a Calendar event after user confirmation.

    Provide the event ID. Show the event details to the user before
    calling with confirm=True.
    """
    event_id = event_id.strip()

    if not event_id:
        return {
            "success": False,
            "error": "Event ID cannot be empty.",
        }

    try:
        service = get_calendar_service()

        if not confirm:
            event = (
                service.events()
                .get(
                    calendarId="primary",
                    eventId=event_id,
                )
                .execute()
            )

            return {
                "success": False,
                "confirmation_required": True,
                "event": {
                    "id": event.get("id", ""),
                    "summary": event.get("summary", "(No title)"),
                    "start": event.get("start", {}),
                    "end": event.get("end", {}),
                    "location": event.get("location", ""),
                    "description": event.get("description", ""),
                    "html_link": event.get("htmlLink", ""),
                    "status": event.get("status", ""),
                },
                "message": (
                    "Show the event details to the user. "
                    "Delete only after explicit approval."
                ),
            }

        service.events().delete(
            calendarId="primary",
            eventId=event_id,
        ).execute()

        return {
            "success": True,
            "message": f"Calendar event {event_id} deleted successfully.",
        }

    except Exception as exc:
        return _error_response("Delete Calendar event", exc)

# ============================================================
# SERVER ENTRY POINT
# ============================================================

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        stream=sys.stderr,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    mcp.run(transport="stdio")
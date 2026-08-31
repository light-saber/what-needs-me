"""Small, read-only adapter around the Gmail API.

All returned messages are normalized into plain dictionaries so the triage layer
has no dependency on Google client objects.
"""

from __future__ import annotations

import base64
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from app.config import google_token_path

GMAIL_SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
ACCOUNT_COLOR = "#7c6cff"


def _service() -> Any:
    """Build an authenticated Gmail client; refreshes an expired OAuth token."""
    token_path = google_token_path()
    if not token_path.is_file():
        raise FileNotFoundError(f"Gmail token file not found at {token_path}")
    credentials = Credentials.from_authorized_user_file(str(token_path), GMAIL_SCOPES)
    if credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())
    if not credentials.valid:
        raise RuntimeError("Gmail credentials are invalid or cannot be refreshed")
    return build("gmail", "v1", credentials=credentials, cache_discovery=False)


def _headers(payload: dict[str, Any]) -> dict[str, str]:
    return {
        item["name"].lower(): item.get("value", "")
        for item in payload.get("headers", [])
        if item.get("name")
    }


def _body_text(part: dict[str, Any]) -> str:
    """Extract the first useful plain-text body, recursively and safely."""
    mime = part.get("mimeType", "")
    data = part.get("body", {}).get("data")
    if data and (mime == "text/plain" or not part.get("parts")):
        return base64.urlsafe_b64decode(data + "=" * (-len(data) % 4)).decode("utf-8", "replace")
    for child in part.get("parts", []):
        text = _body_text(child)
        if text:
            return text
    return ""


def _date(raw: dict[str, Any], headers: dict[str, str]) -> str:
    try:
        return datetime.fromtimestamp(int(raw["internalDate"]) / 1000, tz=timezone.utc).isoformat()
    except (KeyError, TypeError, ValueError):
        try:
            return parsedate_to_datetime(headers.get("date", "")).astimezone(timezone.utc).isoformat()
        except (TypeError, ValueError):
            return ""


def _normalize(raw: dict[str, Any], account_id: str) -> dict[str, Any]:
    payload = raw.get("payload", {})
    headers = _headers(payload)
    return {
        "id": raw["id"],
        "threadId": raw["threadId"],
        "accountId": account_id,
        "from": headers.get("from", "Unknown sender"),
        "subject": headers.get("subject", "(no subject)"),
        "date": _date(raw, headers),
        "snippet": raw.get("snippet", ""),
        "body": _body_text(payload),
        "labels": raw.get("labelIds", []),
        "headers": {"list-unsubscribe": headers.get("list-unsubscribe", "")},
    }


def list_accounts() -> list[dict[str, str]]:
    service = _service()
    profile = service.users().getProfile(userId="me").execute()
    email = profile["emailAddress"]
    return [{"id": email, "email": email, "label": email, "color": ACCOUNT_COLOR}]


def fetch_recent_messages(days: int = 7, cap: int = 200) -> list[dict[str, Any]]:
    """Fetch recent inbox messages only; this never changes Gmail state."""
    service = _service()
    profile = service.users().getProfile(userId="me").execute()
    account_id = profile["emailAddress"]
    response = service.users().messages().list(
        userId="me", q=f"in:inbox newer_than:{max(1, days)}d", maxResults=min(max(1, cap), 200)
    ).execute()
    return [
        _normalize(
            service.users().messages().get(userId="me", id=item["id"], format="full").execute(), account_id
        )
        for item in response.get("messages", [])
    ]


def fetch_thread(thread_id: str) -> dict[str, Any]:
    service = _service()
    profile = service.users().getProfile(userId="me").execute()
    raw = service.users().threads().get(userId="me", id=thread_id, format="full").execute()
    messages = [_normalize(message, profile["emailAddress"]) for message in raw.get("messages", [])]
    return {"id": thread_id, "messages": messages}


if __name__ == "__main__":
    accounts = list_accounts()
    messages = fetch_recent_messages()
    print(f"{accounts[0]['email']}: fetched {len(messages)} messages")

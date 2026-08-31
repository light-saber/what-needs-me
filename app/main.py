"""FastAPI entry point for the read-only mail triage app."""

from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles

from app.gmail_client import fetch_recent_messages, fetch_thread, list_accounts
from app.summarizer import summarize_thread
from app.triage import build_pile, make_cards

app = FastAPI(title="What Needs Me")
STATIC_DIR = Path(__file__).parent / "static"
STATIC_DIR.mkdir(exist_ok=True)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


def _gmail_error(error: Exception) -> HTTPException:
    """Give clients a safe operational error without leaking credential details."""
    return HTTPException(status_code=503, detail=f"Gmail is unavailable: {type(error).__name__}")


@app.get("/api/accounts")
def accounts() -> list[dict[str, str]]:
    try:
        return list_accounts()
    except Exception as error:
        raise _gmail_error(error) from error


@app.get("/api/today")
def today(
    mode: Literal["fused", "split"] = "fused", days: int = Query(default=7, ge=1, le=90)
) -> dict[str, object]:
    try:
        messages = fetch_recent_messages(days=days)
        # In fused mode, newsletters and promotions with the same source and
        # subject are one item even when a future multi-account client fetches both.
        if mode == "fused":
            deduped: dict[tuple[str, str], dict] = {}
            for message in messages:
                labels = {item.upper() for item in message.get("labels", [])}
                is_promo = message.get("headers", {}).get("list-unsubscribe") or "CATEGORY_PROMOTIONS" in labels
                key = (message.get("from", "").lower(), message.get("subject", "").strip().lower()) if is_promo else (message["id"], "")
                deduped.setdefault(key, message)
            messages = list(deduped.values())
        return {
            "date": datetime.now(timezone.utc).date().isoformat(),
            "cards": make_cards(messages),
            "pile": {"categories": build_pile(messages)},
        }
    except Exception as error:
        raise _gmail_error(error) from error


@app.get("/api/thread/{thread_id}")
def thread(thread_id: str) -> dict[str, object]:
    try:
        messages = fetch_thread(thread_id).get("messages", [])
        return {
            "summary": summarize_thread(messages),
            "changed_since_last_seen": "Nothing new since your last view.",
            "messages": [
                {"from": item["from"], "date": item["date"], "snippet": item["snippet"], "subject": item["subject"]}
                for item in messages[-10:]
            ],
        }
    except Exception as error:
        raise _gmail_error(error) from error


app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")

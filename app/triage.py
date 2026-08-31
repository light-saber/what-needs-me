"""Deterministic mail triage with no network or provider dependencies."""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone
from email.utils import parseaddr
from typing import Any, Iterable

AMOUNT_RE = re.compile(r"(?:₹\s?\d[\d,]*|\bINR\s?\d[\d,]*|\bRs\.?\s?\d[\d,]*|\$\s?\d[\d,]*)", re.I)
DATE_RE = re.compile(r"(?:by|due|before|reply by)\s+([A-Z][a-z]+\.?\s+\d{1,2}(?:,?\s+\d{4})?|\d{1,2}[/-]\d{1,2}(?:[/-]\d{2,4})?)", re.I)
ACTION_RE = re.compile(r"\b(approve|review|sign off|confirm|action required|needs your approval|reply|respond)\b", re.I)
AUTOMATED_RE = re.compile(r"no.?reply|do.?not.?reply|notification|alert|mailer-daemon", re.I)


def _text(message: dict[str, Any]) -> str:
    return f"{message.get('subject', '')}\n{message.get('body', message.get('snippet', ''))[:500]}"


def classify(message: dict[str, Any], sender_counts: Counter[str] | None = None) -> str:
    text = _text(message)
    subject = message.get("subject", "")
    sender = message.get("from", "")
    labels = {label.upper() for label in message.get("labels", [])}
    headers = {key.lower(): value for key, value in message.get("headers", {}).items()}
    if re.search(r"\b(invoice|payment|statement|premium|recharge|renewal)\b", text, re.I) and (
        AMOUNT_RE.search(text) or re.search(r"\b(due|by|before)\b", text, re.I)
    ):
        return "bill_payment"
    if re.search(r"\b(approve|review|sign off|confirm|action required|needs your approval)\b", text, re.I):
        return "approval"
    if re.search(r"\b(booking|flight|hotel|pnr|boarding pass|itinerary|trip)\b", text, re.I):
        return "travel"
    if headers.get("list-unsubscribe") or "CATEGORY_PROMOTIONS" in labels:
        return "newsletter"
    if AUTOMATED_RE.search(sender):
        return "notification"
    if re.search(r"\b(receipt|order confirmation|payment confirmation|transaction)\b", subject, re.I):
        return "receipt"
    address = parseaddr(sender)[1].lower()
    count = sender_counts[address] if sender_counts and address else 1
    if address and not AUTOMATED_RE.search(sender) and count <= 3:
        return "personal"
    return "unknown"


def _parse_date(value: str, today: date) -> str | None:
    value = value.strip().replace(".", "")
    for fmt in ("%B %d %Y", "%b %d %Y", "%B %d", "%b %d", "%d/%m/%Y", "%d-%m-%Y", "%m/%d/%Y"):
        try:
            parsed = datetime.strptime(value.replace(",", ""), fmt).date()
            if "%Y" not in fmt:
                parsed = parsed.replace(year=today.year)
                if parsed < today - timedelta(days=30):
                    parsed = parsed.replace(year=today.year + 1)
            return datetime.combine(parsed, datetime.min.time(), tzinfo=timezone.utc).isoformat()
        except ValueError:
            continue
    return None


def extract_ask_deadline(message: dict[str, Any], today: date | None = None) -> tuple[str | None, str | None]:
    """Return a concise action and ISO deadline from a normalized message."""
    today = today or datetime.now(timezone.utc).date()
    text = _text(message)
    deadline_ts = None
    deadline_label = None
    relative = re.search(r"\b(?:EOD|COB)\s+(today|tomorrow)\b|\b(today|tomorrow)\b", text, re.I)
    dated = DATE_RE.search(text)
    if dated:
        deadline_label = dated.group(1)
        deadline_ts = _parse_date(deadline_label, today)
    elif relative:
        word = next(group for group in relative.groups() if group).lower()
        due = today + timedelta(days=1 if word == "tomorrow" else 0)
        deadline_label = word
        deadline_ts = datetime.combine(due, datetime.min.time(), tzinfo=timezone.utc).isoformat()
    amount = AMOUNT_RE.search(text)
    action = ACTION_RE.search(text)
    if amount and (re.search(r"\b(pay|payment|invoice|due)\b", text, re.I)):
        ask = f"Pay {amount.group(0).replace(' ', '')}"
    elif action:
        ask = action.group(1).capitalize()
    elif deadline_ts:
        ask = "Respond"
    else:
        return None, None
    if deadline_label:
        ask += f" by {deadline_label}"
    return ask, deadline_ts


def _urgency(category: str, deadline_ts: str | None) -> str:
    if category == "bill_payment" and deadline_ts:
        return "high"
    if category == "approval" and deadline_ts:
        return "high"
    if category in {"bill_payment", "approval", "personal", "travel"}:
        return "medium"
    return "low"


def make_cards(messages: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    messages = list(messages)
    counts = Counter(parseaddr(item.get("from", ""))[1].lower() for item in messages)
    cards = []
    for message in messages:
        category = classify(message, counts)
        ask, deadline_ts = extract_ask_deadline(message)
        actionable = category in {"bill_payment", "approval", "travel", "personal"} or ask is not None
        if not actionable:
            continue
        cards.append({
            "id": message["id"], "threadId": message["threadId"], "accountId": message.get("accountId", "default"),
            "category": category, "subject": message.get("subject", "(no subject)"),
            "ask": ask or ("Review travel details" if category == "travel" else "Read and respond"),
            "deadline": deadline_ts, "deadline_ts": deadline_ts, "sender": message.get("from", "Unknown sender"),
            "snippet": message.get("snippet", ""), "date": message.get("date", ""),
            "urgency": _urgency(category, deadline_ts),
        })
    return rank(cards)


def rank(cards: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    weights = {"bill_payment": 0, "approval": 1, "personal": 2, "travel": 3, "unknown": 4}
    return sorted(cards, key=lambda card: (weights.get(card["category"], 5), 0 if card.get("deadline_ts") else 1, card.get("date", "")), reverse=False)


def build_pile(messages: Iterable[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    messages = list(messages)
    counts = Counter(parseaddr(item.get("from", ""))[1].lower() for item in messages)
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for message in messages:
        category = classify(message, counts)
        ask, _ = extract_ask_deadline(message)
        if category in {"newsletter", "receipt", "notification"} or (category == "unknown" and not ask):
            groups[category].append(message)
    return {
        category: {
            "count": len(items),
            "summary": f"{len(items)} {category.replace('_', ' ')} message{'s' if len(items) != 1 else ''}",
            "latest": max((item.get("date", "") for item in items), default=""),
        }
        for category, items in groups.items()
    }

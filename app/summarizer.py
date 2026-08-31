"""Optional Gemini-powered thread compression with a deterministic fallback."""

from __future__ import annotations

import os
from typing import Any


def fallback_summary(messages: list[dict[str, Any]]) -> str:
    if not messages:
        return "No messages in this thread."
    snippets = [message.get("snippet", "").strip() for message in messages[-2:] if message.get("snippet", "").strip()]
    return " ".join(snippets)[:600] or "Thread details are unavailable."


def summarize_thread(messages: list[dict[str, Any]]) -> str:
    """Use Gemini only when explicitly configured; failure always falls back."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return fallback_summary(messages)
    try:
        from google import genai

        prompt = "Compress this email thread into one short paragraph. Focus on the current ask and change:\n" + "\n".join(
            f"{item.get('from', '')}: {item.get('snippet', '')}" for item in messages
        )
        response: Any = genai.Client(api_key=api_key).models.generate_content(model="gemini-2.0-flash", contents=prompt)
        return response.text.strip() if response.text else fallback_summary(messages)
    except Exception:
        return fallback_summary(messages)

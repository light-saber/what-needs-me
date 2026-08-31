"""Runtime configuration."""

from __future__ import annotations

import os
from pathlib import Path


def google_token_path() -> Path:
    """Return the OAuth token location without reading or exposing its contents."""
    return Path(os.environ.get("GOOGLE_TOKEN_PATH", "~/.hermes/google_token.json")).expanduser()

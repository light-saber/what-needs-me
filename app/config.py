"""Runtime configuration."""

from __future__ import annotations

import os
from pathlib import Path


def google_token_path() -> Path:
    """Return the OAuth token location without reading or exposing its contents.

    Defaults to the repo-relative 'secrets/gmail_token.json' (gitignored);
    override with the GOOGLE_TOKEN_PATH environment variable.
    """
    return Path(os.environ.get("GOOGLE_TOKEN_PATH", "secrets/gmail_token.json")).expanduser()

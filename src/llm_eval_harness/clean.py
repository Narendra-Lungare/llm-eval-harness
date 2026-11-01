"""Text normalisation.

Every character offset we ever report (golden spans, chunk spans, citations)
is relative to the *normalised* text produced here, so this function must stay
deterministic. If you change it, bump the manifest schema version: old offsets
become invalid.
"""

from __future__ import annotations

import re
import unicodedata

_WHITESPACE_RUN = re.compile(r"[ \t]{2,}")
_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")


def normalize(text: str) -> str:
    """Normalise line endings, unicode form, and blank-line runs."""
    text = unicodedata.normalize("NFKC", text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = _CONTROL_CHARS.sub("", text)

    out: list[str] = []
    blank_run = 0
    for raw_line in text.split("\n"):
        line = _WHITESPACE_RUN.sub(" ", raw_line.rstrip())
        if not line.strip():
            blank_run += 1
            if blank_run > 1:
                continue
        else:
            blank_run = 0
        out.append(line)

    return "\n".join(out).strip()


def title_from(text: str, fallback: str) -> str:
    """Use the first markdown heading, else the first non-empty line."""
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("#"):
            return stripped.lstrip("#").strip()[:120]
        return stripped[:120]
    return fallback

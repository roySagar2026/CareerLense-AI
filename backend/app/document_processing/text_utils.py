"""Text normalisation helpers shared by parsers and the NLP engine."""

from __future__ import annotations

import re
import unicodedata

BULLET_CHARS = "•◦▪▫●○■□‣⁃∙·►➢➤✓✔*"
_BULLET_RE = re.compile(rf"^\s*(?:[{re.escape(BULLET_CHARS)}]|[-–—](?=\s))\s*")
_ZERO_WIDTH = dict.fromkeys(map(ord, "​‌‍⁠﻿"), None)
_WS_RE = re.compile(r"[ \t ]+")


def normalize_line(text: str) -> str:
    """NFKC-normalise (fixes ligatures), drop zero-width chars and collapse spaces."""
    text = unicodedata.normalize("NFKC", text).translate(_ZERO_WIDTH)
    return _WS_RE.sub(" ", text).strip()


def split_bullet(text: str) -> tuple[str, bool]:
    """Return (text without bullet marker, was_bullet)."""
    match = _BULLET_RE.match(text)
    if not match:
        return text.strip(), False
    return text[match.end() :].strip(), True


def merge_wrapped_lines(lines: list[str]) -> list[str]:
    """Join wrapped continuation lines onto the previous bullet/sentence.

    A line is a continuation only when it clearly continues the previous one
    (starts lowercase/digit/punctuation and the previous line was long), so real
    headings and new bullets are never swallowed.
    """
    merged: list[str] = []
    for raw in lines:
        line = raw.strip()
        if not line:
            continue
        _, is_bullet = split_bullet(line)
        if merged and not is_bullet and len(merged[-1]) >= 55 and (line[0].islower() or line[0] in ",;)(&"):
            merged[-1] = f"{merged[-1]} {line}"
        else:
            merged.append(line)
    return merged


def word_count(text: str) -> int:
    return len(re.findall(r"[A-Za-z0-9][A-Za-z0-9+#.'-]*", text))


def normalize_term(text: str) -> str:
    """Lower-case alphanumeric key used for loose comparisons."""
    return re.sub(r"[^a-z0-9+#.]+", " ", text.lower()).strip()

"""Turn a job-posting HTML page into plain text (stdlib only), preferring schema.org JobPosting data."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from html.parser import HTMLParser

_SKIP = {"script", "style", "noscript", "svg", "nav", "footer", "header", "form", "iframe", "template"}
_BLOCK = {"p", "div", "br", "section", "article", "ul", "ol", "h1", "h2", "h3", "h4", "h5", "h6", "tr", "table"}


@dataclass
class ExtractedPage:
    title: str | None
    text: str
    company: str | None = None
    location: str | None = None


class _TextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.ld_json: list[str] = []
        self.title = ""
        self._skip_depth = 0
        self._in_title = False
        self._in_ld = False
        self._ld_buffer: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "script" and (dict(attrs).get("type") or "").lower() == "application/ld+json":
            self._in_ld, self._ld_buffer = True, []
            return
        if tag == "title":
            self._in_title = True
        if tag in _SKIP:
            self._skip_depth += 1
        elif tag == "li":
            self.parts.append("\n- ")
        elif tag in _BLOCK:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag == "script" and self._in_ld:
            self.ld_json.append("".join(self._ld_buffer))
            self._in_ld = False
            return
        if tag == "title":
            self._in_title = False
        if tag in _SKIP:
            self._skip_depth = max(0, self._skip_depth - 1)
        elif tag in _BLOCK or tag == "li":
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self._in_ld:
            self._ld_buffer.append(data)
        elif self._in_title:
            self.title += data
        elif not self._skip_depth:
            self.parts.append(data)


def _clean(text: str) -> str:
    text = re.sub(r"[ \t ]+", " ", text)
    text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)
    return "\n".join(line.strip() for line in text.splitlines()).strip()


def html_to_text(html: str) -> str:
    parser = _TextParser()
    parser.feed(html)
    return _clean("".join(parser.parts))


def _find_job_posting(node: object) -> dict | None:
    if isinstance(node, list):
        for item in node:
            found = _find_job_posting(item)
            if found:
                return found
    elif isinstance(node, dict):
        kind = node.get("@type")
        if kind == "JobPosting" or (isinstance(kind, list) and "JobPosting" in kind):
            return node
        return _find_job_posting(node.get("@graph", []))
    return None


def extract_page(html: str) -> ExtractedPage:
    parser = _TextParser()
    parser.feed(html)
    page_text = _clean("".join(parser.parts))
    title = _clean(parser.title) or None
    for raw in parser.ld_json:
        try:
            posting = _find_job_posting(json.loads(raw))
        except ValueError:
            continue
        if posting and posting.get("description"):
            description = html_to_text(str(posting["description"]))
            org = posting.get("hiringOrganization")
            location = posting.get("jobLocation")
            if isinstance(location, list) and location:
                location = location[0]
            address = location.get("address", {}) if isinstance(location, dict) else {}
            place = ", ".join(
                str(address[k]) for k in ("addressLocality", "addressRegion", "addressCountry") if address.get(k)
            )
            return ExtractedPage(
                title=str(posting.get("title") or title or "") or None,
                text=description,
                company=org.get("name") if isinstance(org, dict) else None,
                location=place or None,
            )
    return ExtractedPage(title=title, text=page_text)

"""SSRF-guarded fetching of public job-posting URLs.

Defences: http/https only, no embedded credentials, standard ports only, every resolved
address must be globally routable (blocks loopback, private, link-local, cloud metadata,
CGNAT, multicast), redirects are followed manually and re-validated (max 3), response size
and time are capped, and only text-like content types are accepted.

Residual risk: DNS can change between our check and the connection (DNS rebinding). The
serverless runtime has no internal network to reach, which limits the impact; container
deployments should additionally restrict egress at the network layer.
"""

from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urljoin, urlsplit

import httpx

from app.core.errors import AppError

MAX_BYTES = 1_500_000
MAX_REDIRECTS = 3
TIMEOUT_SECONDS = 10.0
_ALLOWED_TYPES = ("text/html", "application/xhtml+xml", "text/plain")
_BLOCKED_SUFFIXES = (".local", ".internal", ".localhost", ".lan", ".intranet", ".corp", ".home")
USER_AGENT = "CareerLensBot/1.0 (+job description import; user initiated)"


def _blocked(message: str) -> AppError:
    return AppError(422, "url_blocked", message)


def validate_public_url(url: str) -> str:
    """Raise AppError(url_blocked) unless `url` is a public http(s) address. Returns the URL."""
    parts = urlsplit(url.strip())
    if parts.scheme not in {"http", "https"}:
        raise _blocked("Only http and https links can be imported.")
    host = (parts.hostname or "").lower().rstrip(".")
    if not host:
        raise _blocked("The link has no host name.")
    if parts.username or parts.password:
        raise _blocked("Links with embedded credentials are not allowed.")
    try:
        port = parts.port
    except ValueError as exc:
        raise _blocked("The link has an invalid port.") from exc
    if port not in (None, 80, 443):
        raise _blocked("Only standard web ports (80/443) are allowed.")
    if host == "localhost" or host.endswith(_BLOCKED_SUFFIXES) or ("." not in host and not _is_ip(host)):
        raise _blocked("Local and internal addresses cannot be imported.")
    try:
        infos = socket.getaddrinfo(host, port or (443 if parts.scheme == "https" else 80), type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise AppError(422, "fetch_failed", "That address could not be resolved. Paste the job text instead.") from exc
    for info in infos:
        address = ipaddress.ip_address(info[4][0])
        mapped = getattr(address, "ipv4_mapped", None)
        address = mapped or address
        if not address.is_global or address.is_multicast:
            raise _blocked("Local and internal addresses cannot be imported.")
    return url.strip()


def _is_ip(host: str) -> bool:
    try:
        ipaddress.ip_address(host)
    except ValueError:
        return False
    return True


def fetch_public_page(url: str) -> tuple[str, str]:
    """Return (final_url, html). Raises AppError with a user-readable message on any failure."""
    current = validate_public_url(url)
    headers = {"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml;q=0.9,text/plain;q=0.8"}
    try:
        with httpx.Client(follow_redirects=False, timeout=TIMEOUT_SECONDS, headers=headers) as client:
            for _ in range(MAX_REDIRECTS + 1):
                with client.stream("GET", current) as response:
                    if response.status_code in {301, 302, 303, 307, 308}:
                        location = response.headers.get("location")
                        if not location:
                            raise AppError(422, "fetch_failed", "The site redirected without a destination.")
                        current = validate_public_url(urljoin(current, location))
                        continue
                    if response.status_code in {401, 403, 429} or response.status_code >= 400:
                        raise AppError(
                            422,
                            "fetch_failed",
                            f"The site refused automated access (HTTP {response.status_code}). "
                            "Paste the job description text instead.",
                        )
                    content_type = response.headers.get("content-type", "").split(";")[0].strip().lower()
                    if content_type and content_type not in _ALLOWED_TYPES:
                        raise AppError(422, "fetch_failed", f"Unsupported content type '{content_type}'.")
                    body = bytearray()
                    for chunk in response.iter_bytes():
                        body.extend(chunk)
                        if len(body) > MAX_BYTES:
                            raise AppError(422, "fetch_failed", "The page is too large to import.")
                    encoding = response.encoding or "utf-8"
                    return current, bytes(body).decode(encoding, errors="replace")
            raise AppError(422, "fetch_failed", "The link redirected too many times.")
    except httpx.TimeoutException as exc:
        raise AppError(422, "fetch_failed", "The site took too long to respond. Paste the text instead.") from exc
    except httpx.HTTPError as exc:
        raise AppError(422, "fetch_failed", "The page could not be downloaded. Paste the text instead.") from exc

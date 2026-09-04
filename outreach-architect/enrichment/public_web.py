"""
enrichment/public_web.py
Fetch publicly available pages a company publishes about itself.

Unlike the scraper this replaces, it:

* checks ``robots.txt`` before every fetch and honours a disallow
* sends a truthful, identifying User-Agent rather than impersonating a browser
* rate-limits itself per host
* never authenticates, and refuses hosts whose terms forbid automated access
* refuses private, loopback and link-local addresses, so a lead-supplied URL
  cannot be used to probe internal services (SSRF)

The last point matters: ``company_website`` arrives from user input and is
fetched server-side. The previous code passed such URLs straight to
``httpx.get``.
"""

from __future__ import annotations

import asyncio
import ipaddress
import socket
import time
from typing import Any
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import httpx
from bs4 import BeautifulSoup
from loguru import logger

from enrichment.base import EnrichmentProvider, EnrichmentResult

USER_AGENT = "OutreachArchitect/1.0 (+https://github.com/daniellopez882/Outreach-Pro-Agent)"

# Hosts whose terms of service forbid automated collection. Requests to these
# are refused rather than attempted; see docs/data-sourcing.md.
BLOCKED_HOSTS = frozenset(
    {
        "linkedin.com",
        "www.linkedin.com",
        "facebook.com",
        "www.facebook.com",
        "instagram.com",
        "www.instagram.com",
        "x.com",
        "twitter.com",
    }
)

MIN_SECONDS_BETWEEN_REQUESTS = 2.0
MAX_BYTES = 512_000
REQUEST_TIMEOUT = 15.0


def _is_public_address(host: str) -> bool:
    """False for loopback, private, link-local and reserved addresses."""
    try:
        infos = socket.getaddrinfo(host, None)
    except (socket.gaierror, UnicodeError):
        return False
    for info in infos:
        try:
            addr = ipaddress.ip_address(info[4][0])
        except ValueError:
            return False
        if addr.is_private or addr.is_loopback or addr.is_link_local or addr.is_reserved:
            return False
    return True


class PublicWebProvider(EnrichmentProvider):
    """Read a company's own public pages, politely."""

    name = "public_web"
    requires_credentials = False
    terms_compliant = True

    def __init__(self, client: httpx.AsyncClient | None = None) -> None:
        self._client = client
        self._owns_client = client is None
        self._last_request: dict[str, float] = {}
        self._robots: dict[str, RobotFileParser] = {}

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=REQUEST_TIMEOUT,
                follow_redirects=True,
                headers={"User-Agent": USER_AGENT, "Accept-Language": "en-US,en;q=0.9"},
            )
        return self._client

    async def aclose(self) -> None:
        if self._client is not None and self._owns_client:
            await self._client.aclose()
            self._client = None

    async def _robots_allow(self, url: str) -> bool:
        parsed = urlparse(url)
        origin = f"{parsed.scheme}://{parsed.netloc}"
        parser = self._robots.get(origin)

        if parser is None:
            parser = RobotFileParser()
            parser.set_url(f"{origin}/robots.txt")
            try:
                client = await self._get_client()
                response = await client.get(f"{origin}/robots.txt")
                if response.status_code == 200:
                    parser.parse(response.text.splitlines())
                else:
                    # No robots.txt is permission by omission, per RFC 9309.
                    parser.parse([])
            except httpx.HTTPError as exc:
                logger.warning(f"robots.txt unreachable for {origin}: {exc}")
                parser.parse([])
            self._robots[origin] = parser

        return parser.can_fetch(USER_AGENT, url)

    async def _throttle(self, host: str) -> None:
        last = self._last_request.get(host)
        if last is not None:
            elapsed = time.monotonic() - last
            if elapsed < MIN_SECONDS_BETWEEN_REQUESTS:
                await asyncio.sleep(MIN_SECONDS_BETWEEN_REQUESTS - elapsed)
        self._last_request[host] = time.monotonic()

    async def _fetch(self, url: str) -> tuple[str | None, str | None]:
        """Return (html, error)."""
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return None, f"unsupported scheme: {parsed.scheme or '(none)'}"

        host = parsed.hostname or ""
        if host.lower() in BLOCKED_HOSTS:
            return None, (
                f"{host} forbids automated collection in its terms of service; "
                "use a licensed provider instead"
            )
        if not _is_public_address(host):
            return None, f"refusing to fetch a non-public address: {host}"
        if not await self._robots_allow(url):
            return None, f"robots.txt disallows fetching {url}"

        await self._throttle(host)
        try:
            client = await self._get_client()
            response = await client.get(url)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            return None, f"fetch failed: {exc}"

        content_type = response.headers.get("content-type", "")
        if "html" not in content_type:
            return None, f"not an HTML document: {content_type or 'unknown'}"

        return response.text[:MAX_BYTES], None

    @staticmethod
    def _extract(html: str) -> dict[str, Any]:
        soup = BeautifulSoup(html, "html.parser")
        out: dict[str, Any] = {}

        if soup.title and soup.title.string:
            out["page_title"] = soup.title.string.strip()[:200]

        for attrs in ({"name": "description"}, {"property": "og:description"}):
            tag = soup.find("meta", attrs=attrs)
            if tag and tag.get("content"):
                out["description"] = tag["content"].strip()[:500]
                break

        headings = [h.get_text(strip=True) for h in soup.find_all(["h1", "h2"])[:8]]
        if headings:
            out["headings"] = [h[:120] for h in headings if h]

        return out

    async def enrich_person(self, identifier: str, **context: Any) -> EnrichmentResult:
        """
        Not supported. Individuals are not enriched from scraped pages: the
        compliant route for person-level data is a licensed provider or the
        person's own submission.
        """
        return EnrichmentResult.failed(
            self.name,
            identifier,
            "person enrichment is not supported by this provider; "
            "use 'manual' or a licensed vendor",
        )

    async def enrich_company(self, identifier: str, **context: Any) -> EnrichmentResult:
        url = context.get("company_website") or identifier
        if not url:
            return EnrichmentResult.failed(self.name, identifier, "no company website supplied")
        if not str(url).startswith("http"):
            url = f"https://{url}"

        html, error = await self._fetch(str(url))
        if error:
            return EnrichmentResult.failed(self.name, identifier, error)

        data = self._extract(html or "")
        if not data:
            return EnrichmentResult.failed(self.name, identifier, "no usable content on the page")

        data["url"] = str(url)
        return EnrichmentResult(
            source=self.name,
            subject=identifier,
            data=data,
            confidence=min(1.0, len(data) / 4),
            partial=len(data) < 3,
        )

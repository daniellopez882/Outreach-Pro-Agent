"""
Every redirect hop is checked, not just the URL the lead supplied.

Reproduced defect: ``PublicWebProvider`` validated the supplied host (scheme,
blocked list, public address) and then fetched with ``follow_redirects=True``.
A public site that answered ``302 Location: http://169.254.169.254/...`` was
followed straight to the cloud metadata service: the SSRF guard ran once and
the client's redirect handling ran outside it.
"""

from __future__ import annotations

import httpx
import pytest

import enrichment.public_web as public_web
from enrichment.public_web import PublicWebProvider

METADATA = "http://169.254.169.254/latest/meta-data/"


@pytest.fixture
def fast(monkeypatch):
    monkeypatch.setattr(public_web, "MIN_SECONDS_BETWEEN_REQUESTS", 0)
    # DNS is not consulted in the suite: only these two names count as public.
    monkeypatch.setattr(
        public_web, "_is_public_address", lambda host: host in {"example.com", "www.example.com"}
    )


def _provider(handler):
    seen: list[str] = []

    def recording(request: httpx.Request) -> httpx.Response:
        seen.append(str(request.url))
        if request.url.path == "/robots.txt":
            return httpx.Response(404)
        return handler(request)

    client = httpx.AsyncClient(transport=httpx.MockTransport(recording))
    return PublicWebProvider(client=client), seen


class TestRedirects:
    async def test_a_redirect_to_the_metadata_service_is_refused(self, fast):
        def handler(request: httpx.Request) -> httpx.Response:
            if request.url.host == "example.com":
                return httpx.Response(302, headers={"Location": METADATA})
            return httpx.Response(
                200, headers={"content-type": "text/html"}, text="<title>x</title>"
            )

        provider, seen = _provider(handler)
        html, error = await provider._fetch("http://example.com/")
        assert html is None
        assert "non-public" in error
        assert all("169.254.169.254" not in url for url in seen)

    async def test_a_redirect_to_a_blocked_host_is_refused(self, fast):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(301, headers={"Location": "https://www.linkedin.com/company/x"})

        provider, seen = _provider(handler)
        html, error = await provider._fetch("http://example.com/")
        assert html is None
        assert "linkedin.com" in error
        assert all("linkedin" not in url for url in seen)

    async def test_a_redirect_to_another_public_page_is_followed(self, fast):
        def handler(request: httpx.Request) -> httpx.Response:
            if request.url.host == "example.com":
                return httpx.Response(302, headers={"Location": "https://www.example.com/about"})
            return httpx.Response(
                200, headers={"content-type": "text/html"}, text="<title>About us</title>"
            )

        provider, seen = _provider(handler)
        html, error = await provider._fetch("http://example.com/")
        assert error is None
        assert "About us" in html
        assert seen[-1] == "https://www.example.com/about"

    async def test_redirect_loops_stop(self, fast):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(302, headers={"Location": "http://example.com/again"})

        provider, seen = _provider(handler)
        html, error = await provider._fetch("http://example.com/")
        assert html is None
        assert "redirects" in error
        # The first request plus MAX_REDIRECTS hops, and no more.
        page_requests = [u for u in seen if not u.endswith("/robots.txt")]
        assert len(page_requests) == public_web.MAX_REDIRECTS + 1

    async def test_the_client_does_not_follow_redirects_on_its_own(self):
        provider = PublicWebProvider()
        client = await provider._get_client()
        try:
            assert client.follow_redirects is False
        finally:
            await provider.aclose()

    async def test_an_http_error_is_a_clean_failure(self, fast):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(503)

        provider, _ = _provider(handler)
        html, error = await provider._fetch("http://example.com/")
        assert html is None
        assert "503" in error

"""
Tests for the enrichment provider layer.

Enrichment was previously a single ``LinkedInScraper`` that authenticated with
a username and password. It could not work -- ``login()`` sent no CSRF token,
``httpx.Client`` does not follow redirects by default, and the success check
``'feed' in response.url`` raises ``TypeError`` into a bare ``except`` -- and it
breached the LinkedIn User Agreement regardless.

These tests pin the replacement: a provider interface whose shipped
implementations are compliant, and whose web fetcher cannot be pointed at
internal infrastructure.
"""

from __future__ import annotations

import pytest

from enrichment import (
    EnrichmentResult,
    ManualProvider,
    ProviderUnavailable,
    PublicWebProvider,
    available_providers,
    get_provider,
)
from enrichment.base import EnrichmentProvider
from enrichment.public_web import BLOCKED_HOSTS, _is_public_address
from enrichment.registry import register


class TestRegistry:
    def test_shipped_providers_are_available(self):
        assert set(available_providers()) == {"manual", "public_web"}

    def test_unknown_provider_is_rejected(self):
        with pytest.raises(ProviderUnavailable, match="unknown enrichment provider"):
            get_provider("linkedin_scraper")

    def test_every_shipped_provider_is_terms_compliant(self):
        for name in available_providers():
            assert get_provider(name).terms_compliant is True

    def test_a_non_compliant_provider_cannot_be_registered(self):
        """A comment saying 'use at your own risk' is not a control."""

        class Scraper(EnrichmentProvider):
            name = "some_scraper"
            terms_compliant = False

            async def enrich_person(self, identifier, **context): ...

            async def enrich_company(self, identifier, **context): ...

        with pytest.raises(ValueError, match="terms_compliant=False"):
            register(Scraper)


class TestEnrichmentResult:
    def test_result_with_data_and_no_errors_is_ok(self):
        assert EnrichmentResult(source="s", subject="x", data={"a": 1}).ok is True

    def test_empty_result_is_not_ok(self):
        assert EnrichmentResult(source="s", subject="x").ok is False

    def test_failed_result_carries_the_reason(self):
        r = EnrichmentResult.failed("s", "x", "boom")
        assert r.ok is False and r.errors == ["boom"]

    def test_timestamp_is_timezone_aware_utc(self):
        assert EnrichmentResult(source="s", subject="x").fetched_at.endswith("Z")

    def test_serialises_for_transport(self):
        d = EnrichmentResult(source="s", subject="x", data={"a": 1}).to_dict()
        assert d["ok"] is True and d["source"] == "s"


@pytest.mark.asyncio
class TestManualProvider:
    async def test_returns_operator_supplied_fields(self):
        r = await ManualProvider().enrich_person(
            "jane@acme.com",
            lead={"name": "Jane", "job_title": "VP Sales", "company": "Acme"},
        )
        assert r.ok
        assert r.data["company"] == "Acme"

    async def test_ignores_unknown_fields(self):
        r = await ManualProvider().enrich_person(
            "x", lead={"name": "Jane", "internal_crm_id": "should-not-leak"}
        )
        assert "internal_crm_id" not in r.data

    async def test_drops_empty_values(self):
        r = await ManualProvider().enrich_person(
            "x", lead={"name": "Jane", "company": "", "location": None, "tags": []}
        )
        assert set(r.data) == {"name"}

    async def test_no_data_is_a_clean_failure_not_an_exception(self):
        r = await ManualProvider().enrich_person("x", lead={})
        assert r.ok is False and r.errors

    async def test_confidence_grows_with_completeness(self):
        sparse = await ManualProvider().enrich_person("x", lead={"name": "J"})
        rich = await ManualProvider().enrich_person(
            "x",
            lead={
                "name": "J",
                "job_title": "VP",
                "company": "Acme",
                "location": "SF",
                "industry": "SaaS",
                "company_size": "200",
                "notes": "met at conf",
            },
        )
        assert rich.confidence > sparse.confidence

    async def test_company_enrichment(self):
        r = await ManualProvider().enrich_company(
            "Acme", lead={"company": "Acme", "company_website": "https://acme.com"}
        )
        assert r.ok and r.data["company"] == "Acme"


class TestAddressGuards:
    """A lead-supplied company_website is fetched server-side, so it is an SSRF
    vector. The previous code passed such URLs straight to httpx."""

    @pytest.mark.parametrize(
        "host", ["localhost", "127.0.0.1", "10.0.0.1", "192.168.1.1", "169.254.169.254"]
    )
    def test_private_and_loopback_addresses_are_not_public(self, host):
        assert _is_public_address(host) is False

    def test_cloud_metadata_endpoint_is_blocked(self):
        """169.254.169.254 serves instance credentials on AWS, GCP and Azure."""
        assert _is_public_address("169.254.169.254") is False

    def test_unresolvable_host_is_not_public(self):
        assert _is_public_address("this-host-does-not-exist.invalid") is False


@pytest.mark.asyncio
class TestPublicWebProvider:
    async def test_person_enrichment_is_refused(self):
        r = await PublicWebProvider().enrich_person("someone")
        assert r.ok is False
        assert "not supported" in r.errors[0]

    @pytest.mark.parametrize("host", sorted(BLOCKED_HOSTS)[:4])
    async def test_hosts_that_forbid_automation_are_refused(self, host):
        p = PublicWebProvider()
        _, error = await p._fetch(f"https://{host}/company/acme")
        assert error and "terms of service" in error
        await p.aclose()

    @pytest.mark.parametrize(
        "url", ["file:///etc/passwd", "ftp://example.com/x", "gopher://example.com"]
    )
    async def test_non_http_schemes_are_refused(self, url):
        p = PublicWebProvider()
        _, error = await p._fetch(url)
        assert error and "unsupported scheme" in error
        await p.aclose()

    @pytest.mark.parametrize(
        "url", ["http://127.0.0.1:8000/admin", "http://169.254.169.254/latest/meta-data/"]
    )
    async def test_internal_addresses_are_refused(self, url):
        p = PublicWebProvider()
        _, error = await p._fetch(url)
        assert error and "non-public address" in error
        await p.aclose()

    async def test_missing_website_is_a_clean_failure(self):
        p = PublicWebProvider()
        r = await p.enrich_company("", company_website=None)
        assert r.ok is False
        await p.aclose()

    async def test_extract_pulls_title_and_description(self):
        html = (
            "<html><head><title>Acme Corp</title>"
            '<meta name="description" content="We make widgets."></head>'
            "<body><h1>Widgets</h1><h2>For everyone</h2></body></html>"
        )
        data = PublicWebProvider._extract(html)
        assert data["page_title"] == "Acme Corp"
        assert data["description"] == "We make widgets."
        assert "Widgets" in data["headings"]

    async def test_extract_of_empty_page_returns_nothing(self):
        assert PublicWebProvider._extract("<html></html>") == {}

    async def test_user_agent_identifies_itself(self):
        from enrichment.public_web import USER_AGENT

        assert "OutreachArchitect" in USER_AGENT
        assert "Mozilla" not in USER_AGENT, "must not impersonate a browser"

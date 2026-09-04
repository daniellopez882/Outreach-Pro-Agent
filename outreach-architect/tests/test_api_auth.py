"""
API authentication and configuration tests.

Every endpoint was previously unauthenticated -- including
``POST /campaigns/{id}/send``, which delivers email through the configured
SendGrid account. Anyone able to reach the port could send mail as the
operator. These tests pin that shut.
"""

from __future__ import annotations

import pytest

# Endpoints that must never be reachable without a key. The send endpoint is
# listed first because it is the one with an irreversible effect.
PROTECTED = [
    ("post", "/campaigns/1/send"),
    ("post", "/campaigns"),
    ("post", "/leads"),
    ("get", "/leads"),
    ("get", "/leads/1"),
    ("get", "/campaigns"),
    ("get", "/campaigns/1"),
    ("get", "/analytics/stats"),
    ("post", "/test/kimi"),
]


class TestAuthentication:
    @pytest.mark.parametrize("method,path", PROTECTED)
    def test_rejected_without_a_key(self, client, method, path):
        assert getattr(client, method)(path).status_code == 401

    @pytest.mark.parametrize("method,path", PROTECTED)
    def test_rejected_with_a_wrong_key(self, client, method, path):
        r = getattr(client, method)(path, headers={"X-API-Key": "not-the-key"})
        assert r.status_code == 401

    def test_send_endpoint_is_protected(self, client):
        """Called out separately: this one spends money and cannot be undone."""
        assert client.post("/campaigns/1/send").status_code == 401

    def test_rejection_names_the_scheme(self, client):
        r = client.get("/leads")
        assert r.headers.get("WWW-Authenticate") == "X-API-Key"

    def test_error_body_does_not_leak_the_expected_key(self, client, api_key):
        r = client.get("/leads", headers={"X-API-Key": "wrong"})
        assert api_key not in r.text

    def test_valid_key_is_accepted(self, client, auth_headers):
        assert client.get("/leads", headers=auth_headers).status_code == 200


class TestOperationalEndpoints:
    def test_health_needs_no_key(self, client):
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "healthy"

    def test_ready_needs_no_key(self, client):
        assert client.get("/ready").status_code in (200, 503)

    def test_ready_probes_the_database(self, client):
        checks = client.get("/ready").json()["checks"]
        assert checks["database"]["required"] is True
        assert checks["database"]["ok"] is True

    def test_ready_reports_whether_sending_is_enabled(self, client):
        assert client.get("/ready").json()["checks"]["email_sending"]["enabled"] is False

    def test_llm_credentials_are_not_required_to_be_ready(self, client):
        """The API serves lead and campaign reads without a model configured."""
        assert client.get("/ready").json()["checks"]["llm_credentials"]["required"] is False


class TestOpenApiClaims:
    def test_description_makes_no_unmeasured_performance_claim(self, client):
        """
        The description was "Hyper-personalized cold outreach with 15-20%
        response rates", served in the OpenAPI document as though it were a
        property of the software. Nothing here measures a response rate.
        """
        schema = client.get("/openapi.json").json()
        description = schema["info"].get("description", "")
        for claim in ("15-20%", "response rate", "%"):
            assert claim not in description, f"unmeasured claim in API description: {claim!r}"

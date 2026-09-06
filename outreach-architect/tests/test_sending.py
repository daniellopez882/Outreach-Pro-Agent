"""
Delivery gate for ``POST /campaigns/{id}/send`` and the auto-send path.

Reproduced defect: ``_send_email`` logged "SENDING EMAIL", set the campaign to
SENT and returned success -- without consulting ``EMAIL_SENDING_ENABLED`` and
without contacting any mail provider. The README said the route "refuses
unless EMAIL_SENDING_ENABLED=true"; it did not. Every campaign marked SENT had
not been sent.
"""

from __future__ import annotations

import json

import httpx
import pytest

import mailer
from config import SendingDisabled, SendingNotConfigured, settings
from models import Lead, OutreachCampaign, OutreachStatus

TEST_SENDGRID_KEY = "SG.test-key-not-real"


@pytest.fixture
def campaign(client):
    from main import SessionLocal

    db = SessionLocal()
    lead = Lead(name="Ada Lovelace", email="ada@example.com", company="Analytical Engines")
    db.add(lead)
    db.commit()
    db.refresh(lead)
    campaign = OutreachCampaign(
        lead_id=lead.id,
        subject_line="A note on your engine",
        email_body="Hello Ada,\n\nOne paragraph.\n",
        status=OutreachStatus.READY,
    )
    db.add(campaign)
    db.commit()
    db.refresh(campaign)
    yield campaign
    db.delete(campaign)
    db.delete(lead)
    db.commit()
    db.close()


@pytest.fixture
def sending_enabled(monkeypatch):
    monkeypatch.setattr(settings, "email_sending_enabled", True)
    monkeypatch.setattr(settings, "sendgrid_api_key", TEST_SENDGRID_KEY)
    monkeypatch.setattr(settings, "from_email", "outreach@example.com")
    monkeypatch.setattr(settings, "from_name", "Outreach Architect")


@pytest.fixture
def sendgrid(monkeypatch):
    """A fake SendGrid that accepts everything and records what it was sent."""
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(202, headers={"X-Message-Id": "msg-1"})

    monkeypatch.setattr(mailer, "TRANSPORT", httpx.MockTransport(handler))
    return requests


def _status(campaign_id: int) -> OutreachStatus:
    from main import SessionLocal

    db = SessionLocal()
    try:
        return db.get(OutreachCampaign, campaign_id).status
    finally:
        db.close()


class TestSendingDisabled:
    def test_send_is_refused_when_sending_is_disabled(self, client, auth_headers, campaign):
        r = client.post(f"/campaigns/{campaign.id}/send", headers=auth_headers)
        assert r.status_code == 409, r.text
        assert "EMAIL_SENDING_ENABLED" in r.json()["detail"]

    def test_a_refused_campaign_is_not_marked_sent(self, client, auth_headers, campaign):
        client.post(f"/campaigns/{campaign.id}/send", headers=auth_headers)
        assert _status(campaign.id) == OutreachStatus.READY

    def test_no_provider_request_is_made(self, client, auth_headers, campaign, sendgrid):
        client.post(f"/campaigns/{campaign.id}/send", headers=auth_headers)
        assert sendgrid == []

    def test_enabled_but_unconfigured_is_a_503(
        self, client, auth_headers, campaign, sendgrid, monkeypatch
    ):
        monkeypatch.setattr(settings, "email_sending_enabled", True)
        monkeypatch.setattr(settings, "sendgrid_api_key", None)
        monkeypatch.setattr(settings, "from_email", None)
        r = client.post(f"/campaigns/{campaign.id}/send", headers=auth_headers)
        assert r.status_code == 503, r.text
        assert "SENDGRID_API_KEY" in r.json()["detail"]
        assert "FROM_EMAIL" in r.json()["detail"]
        assert sendgrid == []
        assert _status(campaign.id) == OutreachStatus.READY


class TestSendingEnabled:
    def test_send_delivers_through_sendgrid_and_marks_sent(
        self, client, auth_headers, campaign, sending_enabled, sendgrid
    ):
        r = client.post(f"/campaigns/{campaign.id}/send", headers=auth_headers)
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["status"] == "sent"
        assert body["message_id"] == "msg-1"
        assert body["sent_at"]
        assert _status(campaign.id) == OutreachStatus.SENT

        assert len(sendgrid) == 1
        request = sendgrid[0]
        assert str(request.url) == mailer.SENDGRID_SEND_URL
        assert request.headers["Authorization"] == f"Bearer {TEST_SENDGRID_KEY}"
        payload = json.loads(request.content)
        assert payload["personalizations"][0]["to"][0]["email"] == "ada@example.com"
        assert payload["from"] == {"email": "outreach@example.com", "name": "Outreach Architect"}
        assert payload["subject"] == "A note on your engine"
        assert payload["content"][0]["value"].startswith("Hello Ada")
        assert payload["custom_args"]["campaign_id"] == str(campaign.id)

    def test_a_sent_campaign_cannot_be_sent_twice(
        self, client, auth_headers, campaign, sending_enabled, sendgrid
    ):
        client.post(f"/campaigns/{campaign.id}/send", headers=auth_headers)
        r = client.post(f"/campaigns/{campaign.id}/send", headers=auth_headers)
        assert r.status_code == 400
        assert len(sendgrid) == 1

    def test_provider_rejection_is_a_502_and_leaves_the_status_alone(
        self, client, auth_headers, campaign, sending_enabled, monkeypatch
    ):
        def rejecting(request: httpx.Request) -> httpx.Response:
            return httpx.Response(401, json={"errors": [{"message": "bad key"}]})

        monkeypatch.setattr(mailer, "TRANSPORT", httpx.MockTransport(rejecting))
        r = client.post(f"/campaigns/{campaign.id}/send", headers=auth_headers)
        assert r.status_code == 502, r.text
        assert "401" in r.json()["detail"]
        assert _status(campaign.id) == OutreachStatus.READY

    def test_unreachable_provider_is_a_502(
        self, client, auth_headers, campaign, sending_enabled, monkeypatch
    ):
        def unreachable(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("connection refused", request=request)

        monkeypatch.setattr(mailer, "TRANSPORT", httpx.MockTransport(unreachable))
        r = client.post(f"/campaigns/{campaign.id}/send", headers=auth_headers)
        assert r.status_code == 502, r.text
        assert _status(campaign.id) == OutreachStatus.READY

    def test_the_sendgrid_key_never_appears_in_a_response(
        self, client, auth_headers, campaign, sending_enabled, monkeypatch
    ):
        def rejecting(request: httpx.Request) -> httpx.Response:
            return httpx.Response(500, text="server error")

        monkeypatch.setattr(mailer, "TRANSPORT", httpx.MockTransport(rejecting))
        r = client.post(f"/campaigns/{campaign.id}/send", headers=auth_headers)
        assert TEST_SENDGRID_KEY not in r.text

    def test_ready_reports_sending_enabled(self, client, sending_enabled):
        assert client.get("/ready").json()["checks"]["email_sending"]["enabled"] is True


class TestGateInConfiguration:
    def test_disabled_raises_a_typed_error(self, monkeypatch):
        monkeypatch.setattr(settings, "email_sending_enabled", False)
        with pytest.raises(SendingDisabled):
            settings.require_email_credentials()

    def test_missing_settings_are_named(self, monkeypatch):
        monkeypatch.setattr(settings, "email_sending_enabled", True)
        monkeypatch.setattr(settings, "sendgrid_api_key", None)
        monkeypatch.setattr(settings, "from_email", "x@example.com")
        monkeypatch.setattr(settings, "from_name", None)
        with pytest.raises(SendingNotConfigured, match="SENDGRID_API_KEY, FROM_NAME"):
            settings.require_email_credentials()


class TestOrchestratorSend:
    async def test_send_campaign_email_does_not_mark_sent_when_disabled(self, client, campaign):
        from main import SessionLocal
        from orchestrator import OutreachOrchestrator

        db = SessionLocal()
        try:
            row = db.get(OutreachCampaign, campaign.id)
            with pytest.raises(SendingDisabled):
                await OutreachOrchestrator(db).send_campaign_email(row)
            db.refresh(row)
            assert row.status == OutreachStatus.READY
            assert row.sent_at is None
        finally:
            db.close()


class TestAnalytics:
    def test_no_invented_target_rate_is_served(self, client, auth_headers):
        data = client.get("/analytics/stats", headers=auth_headers).json()
        assert "target_response_rate" not in data
        assert data["response_rate"] == 0

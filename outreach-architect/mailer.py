"""
Delivery of a drafted campaign through SendGrid's v3 Mail Send API.

Why this exists
---------------
``OutreachOrchestrator._send_email`` was a placeholder. It logged
"SENDING EMAIL", set the campaign's status to SENT and returned
``{"success": True}``. It never consulted ``EMAIL_SENDING_ENABLED``, never
checked that SendGrid was configured, and never contacted a mail provider.
Two consequences:

* ``POST /campaigns/{id}/send`` did not refuse when sending was disabled,
  which is what the README and ``/ready`` said it did. Any caller holding the
  API key could flip a campaign to SENT with the flag off.
* Every campaign in the database marked SENT had not been sent.

This module is the one place that delivers. The gate is checked here, the
provider is called here, and the caller marks the campaign SENT only after
the provider has accepted the message.

The HTTP transport is a module attribute so tests can substitute an
``httpx.MockTransport`` without patching the network stack.
"""

from __future__ import annotations

from typing import Any

import httpx
from loguru import logger

from config import settings

SENDGRID_SEND_URL = "https://api.sendgrid.com/v3/mail/send"
REQUEST_TIMEOUT_SECONDS = 20.0

#: Tests set this to an ``httpx.MockTransport``. ``None`` means the real network.
TRANSPORT: httpx.AsyncBaseTransport | None = None


class DeliveryFailed(RuntimeError):
    """The provider did not accept the message, or could not be reached."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


def build_payload(campaign: Any) -> dict[str, Any]:
    """The SendGrid v3 request body for one campaign."""
    return {
        "personalizations": [{"to": [{"email": campaign.lead.email, "name": campaign.lead.name}]}],
        "from": {"email": settings.from_email, "name": settings.from_name},
        "subject": campaign.subject_line,
        "content": [{"type": "text/plain", "value": campaign.email_body}],
        # Lets SendGrid's activity feed be joined back to a campaign row.
        "custom_args": {"campaign_id": str(campaign.id)},
    }


async def deliver(campaign: Any) -> dict[str, Any]:
    """
    Deliver one campaign.

    Raises ``SendingDisabled`` or ``SendingNotConfigured`` (from
    ``settings.require_email_credentials``) before any request is made, and
    ``DeliveryFailed`` if SendGrid does not answer 202.
    """
    settings.require_email_credentials()
    payload = build_payload(campaign)
    headers = {"Authorization": f"Bearer {settings.sendgrid_api_key}"}

    try:
        async with httpx.AsyncClient(
            timeout=REQUEST_TIMEOUT_SECONDS, transport=TRANSPORT
        ) as client:
            response = await client.post(SENDGRID_SEND_URL, json=payload, headers=headers)
    except httpx.HTTPError as exc:
        # Logged, not echoed: the exception text is the provider's, not the caller's.
        logger.error(f"SendGrid unreachable for campaign {campaign.id}: {exc!r}")
        raise DeliveryFailed("Mail provider unreachable.") from exc

    if response.status_code != 202:
        logger.error(
            f"SendGrid rejected campaign {campaign.id}: "
            f"HTTP {response.status_code} {response.text[:500]}"
        )
        raise DeliveryFailed(
            f"Mail provider rejected the message (HTTP {response.status_code}).",
            status_code=response.status_code,
        )

    message_id = response.headers.get("X-Message-Id")
    logger.info(f"Campaign {campaign.id} accepted by SendGrid (message id {message_id})")
    return {"provider": "sendgrid", "message_id": message_id}

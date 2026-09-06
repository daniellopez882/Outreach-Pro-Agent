# ADR 0003 — Delivery is one function, gated in code; a campaign is "sent" only when the provider says so

**Status:** accepted · **Date:** 2026-09-06

## Context

ADR 0001 made sending opt-in: `EMAIL_SENDING_ENABLED` defaults to `false`, and
the README said `POST /campaigns/{id}/send` "refuses unless
EMAIL_SENDING_ENABLED=true". Checking the route while writing the threat model
showed that the code did not do this. `OutreachOrchestrator._send_email` was a
placeholder: it logged "SENDING EMAIL", set the campaign's status to `SENT`,
committed, and returned `{"success": True}`. It read no flag, checked no
credentials, and contacted no provider. Three consequences:

1. A caller holding the API key could flip any campaign to `SENT` with sending
   switched off — the opt-in was a setting nothing read.
2. Every campaign in the database marked `SENT` had not been sent.
3. Two `RuntimeError`s that `Settings.require_email_credentials()` was written
   to raise were raised by nothing, and would have surfaced as a bare 500 if
   they had been.

A fourth defect sat in the same path: `kimi_agent.py` built `OpenAI(api_key=None)`
at import time when no model key was configured, which raises. The send route
imports the orchestrator, which imports that module, so on a deployment without
a model key the route answered 500 — for an action that needs no model at all.

## Decision

1. **One place delivers.** `mailer.deliver(campaign)` calls
   `settings.require_email_credentials()` first, builds the SendGrid v3 request,
   posts it with `httpx`, and raises `DeliveryFailed` unless the provider answers
   202. The SendGrid SDK was declared and never imported; it is gone.
2. **Status follows the provider.** `OutreachOrchestrator.send_campaign_email`
   marks a campaign `SENT` and stamps `sent_at` only after `deliver` returns.
   On any failure the row is untouched, so the operator can retry.
3. **Typed errors, mapped once.** `require_email_credentials()` raises
   `SendingDisabled` (switched off) or `SendingNotConfigured` (switched on, sender
   unset). The route maps them to `409` and `503`; `DeliveryFailed` becomes `502`.
   None of the three echoes provider text or the key.
4. **Auto-send respects the same gate.** With `auto_send=true` and delivery
   switched off, the draft is kept as `pending_review` and the result says why
   (`stages.send.skipped`), rather than reporting a send that did not happen.
5. **The model client is built on first use.** `KimiAgent.client` is a property
   that constructs the provider client only when a key exists; without one the
   agent returns its canned responses, and now marks them `generated_by:
   "canned"` so a canned draft is never mistaken for a model's.
6. **Tests pin all of it.** `tests/test_sending.py` reproduces the original
   behaviour (409 and status unchanged when disabled; 202 → `SENT` through a fake
   transport; 401/500/unreachable → 502 with status unchanged; the key never in a
   response). `tests/test_model_client.py` imports the agent with no key.

## Consequences

- `POST /campaigns/{id}/send` is the only path that changes a campaign to
  `SENT`, and it can only do so with a provider receipt in hand.
- Operators see the deployment's posture in `/ready`
  (`checks.email_sending.enabled`) and, from the dashboard, as "Delivery: On/Off".
- Delivery depends on SendGrid's HTTP API and nothing else; swapping providers
  means changing one function and its payload builder.
- The compliance gap ADR 0001 records — no suppression list, unsubscribe
  handling or consent record — is unchanged. Sending stays off by default for
  that reason; this decision only makes the switch real.

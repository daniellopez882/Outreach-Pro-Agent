# ADR 0001 — Every data and action route authenticates; sending mail is opt-in

**Status:** accepted · **Date:** 2026-09-06 (records the decision made in PR #1)

## Context

Every endpoint was unauthenticated, including `POST /campaigns/{id}/send`.
Reaching the port was sufficient to deliver mail through the operator's
SendGrid account and spend its sending reputation. Five settings were
required fields, so the application could not even be imported without a
full production environment, and `allow_origins=["*"]` was combined with
`allow_credentials=True`, which browsers reject outright.

Separately, the project implements **no suppression list, unsubscribe
handling or consent tracking** — controls cold outreach is legally required to
have (CAN-SPAM, GDPR/PECR, CASL).

## Decision

1. Every route that reads or changes data (`/leads`, `/campaigns`,
   `/campaigns/{id}/send`, `/analytics/stats`, `/test/kimi`) depends on
   `require_api_key`: the `X-API-Key` header compared in constant time against
   `settings.api_key`. Only `/`, `/health` and `/ready` are open.
2. The key has an obviously insecure default (`changeme-in-production`) so
   development works without a secret, and `validate_production_settings()`
   refuses to start in production with that default, with an unset SendGrid
   configuration while sending is enabled, or with an empty CORS list that
   would silently break the frontend.
3. `EMAIL_SENDING_ENABLED` defaults to `false`. Turning it on is an explicit
   operator decision, taken knowing the compliance controls above do not
   exist; `/health` reports the flag so a deployment's posture is visible.
4. CI boots the image and asserts that the send endpoint answers 401 to an
   unauthenticated caller; if the dependency is removed, the build fails.

## Consequences

- One shared key, no per-user identity: adequate for a single-operator tool,
  documented as a limit.
- Development runs with the insecure default and a warning; production
  refuses it. The distinction rests on `ENVIRONMENT`, so that variable must be
  set correctly in deployment.
- Sending mail stays off until someone reads the README's compliance section
  and decides to turn it on.

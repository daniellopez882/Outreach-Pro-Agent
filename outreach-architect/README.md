# Outreach Architect — backend

The FastAPI service behind the root README. This file is the module map; the
root [README](../README.md) has the defects that were reproduced and fixed,
the API table and the configuration reference.

> An earlier version of this file described a "LinkedIn Scraper" component,
> published open, response and meeting rates, and promised "hyper-personalized
> emails that actually get responses". The scraper is gone (it never worked and
> breached LinkedIn's terms — [docs/data-sourcing.md](docs/data-sourcing.md)),
> and no campaign has ever been run with this code, so no rate exists to quote.

## Modules

| File | Does |
|---|---|
| `main.py` | FastAPI app: probes, `X-API-Key` dependency, lead and campaign routes, the send route and its 409/503/502 mapping, analytics counts |
| `config.py` | Typed settings; `validate_production_settings()` refuses an unsafe production start; `require_email_credentials()` is the delivery gate |
| `orchestrator.py` | enrich → analyse → draft → score → store as a `ready` campaign; `send_campaign_email()` marks `SENT` only after a provider receipt |
| `mailer.py` | The one function that delivers: checks the gate, posts to SendGrid's v3 API with `httpx`, raises `DeliveryFailed` unless it answers 202 |
| `kimi_agent.py` | OpenAI-compatible client for Kimi or DeepSeek, built on first use; canned responses without a key, marked `generated_by: "canned"` |
| `enrichment/` | `base.py` interface, `registry.py` compliance gate, `manual.py` (operator data), `public_web.py` (robots.txt-aware fetcher with the SSRF guard applied to every redirect hop) |
| `company_intelligence.py` | NewsAPI lookups when a key is set; hiring signals report `available: False` rather than scraping |
| `models.py` | SQLAlchemy models: `Lead`, `OutreachCampaign`, `FollowUp` |
| `tests/` | 93 offline tests; see the root README's Testing section |

## Run it

```bash
cp .env.example .env            # API_KEY is the only thing you must change for anything but local use
python -m venv .venv && .venv/bin/pip install -r requirements-dev.txt
.venv/bin/pytest
.venv/bin/uvicorn main:app --reload
```

SQLite is the default, so a fresh clone runs with no database to set up. Every
route except `/`, `/health` and `/ready` needs `X-API-Key`.

```bash
curl -s -H "X-API-Key: $API_KEY" localhost:8000/leads
```

## Sending mail

Off by default. `POST /campaigns/{id}/send` answers `409` until
`EMAIL_SENDING_ENABLED=true`, `503` if it is enabled but `SENDGRID_API_KEY`,
`FROM_EMAIL` or `FROM_NAME` is unset, and `502` if SendGrid does not accept the
message. A campaign becomes `sent` only in the remaining case. Read the
compliance note in [docs/data-sourcing.md](docs/data-sourcing.md) before turning
it on: there is no suppression list, unsubscribe handling or consent record here.

## Documents

- [docs/data-sourcing.md](docs/data-sourcing.md) — what is fetched, what is refused, how to add a licensed provider
- [docs/adr/](docs/adr/) — three decision records
- [docs/threat-model.md](docs/threat-model.md) — assets, boundaries, eleven threats, what remains open

# Data sourcing

Where lead data comes from, what this project refuses to do, and how to add a
source that is licensed to give you what you need.

## Position

**This project does not scrape sites whose terms forbid it.** That is enforced
in code, not documented as advice:

- `enrichment/registry.py` refuses to register or construct any provider whose
  `terms_compliant` flag is `False`.
- `enrichment/public_web.py` refuses a fixed set of hosts outright, honours
  `robots.txt`, throttles per host, and sends a User-Agent that identifies the
  tool rather than impersonating a browser.
- `tests/test_enrichment.py` fails the build if either control is removed.

## What was removed, and why

### `linkedin_scraper.py`

Logged into LinkedIn with a username and password, then scraped profiles,
activity and people search.

**It never worked.** Three independent faults:

| Fault | Effect |
|---|---|
| `POST /uas/login-submit` with no CSRF token | LinkedIn rejects the request |
| `httpx.Client` does not follow redirects by default | The post-login redirect was never followed |
| `'feed' in response.url` | `TypeError: argument of type 'URL' is not a container or iterable`, swallowed by a bare `except Exception` |

`login()` could only ever return `False`. Unauthenticated profile fetches then
received LinkedIn's authentication wall, and `_parse_profile_html` parsed *that*
as though it were a profile — so the pipeline was being fed login-page markup.

**It also should not work.** The LinkedIn User Agreement (§8.2) prohibits
automated access, scraping and the use of bots. Credential-based automation
gets accounts restricted or terminated. The original code acknowledged this in
a comment — *"Use at your own risk - LinkedIn may ban accounts for scraping"* —
which is a disclaimer, not a control.

### `CompanyIntelligence.check_hiring_signals`

Scraped `linkedin.com/jobs/search`. Same terms problem, plus it used `re`
without importing it, so every call raised `NameError` into the surrounding
`except Exception` and reported "no hiring data" whether or not the company was
hiring. It now returns `available: False` with an explanation, rather than
appearing to have looked.

## What ships instead

| Provider | Source | Credentials | Notes |
|---|---|---|---|
| `manual` | Fields already on the lead | none | Default. A CRM export or signup form usually carries enough to personalise. |
| `public_web` | The company's own website | none | robots.txt-aware, rate-limited, HTML only, ≤512 KB. |

`public_web` deliberately does **not** do person-level enrichment. There is no
compliant way to collect information about an individual by scraping; the
lawful routes are the person's own submission, or a vendor licensed to
redistribute it.

## SSRF

`company_website` arrives from user input and is fetched by the server, which
makes it a server-side request forgery vector. The previous code passed such
URLs straight to `httpx.get`.

`public_web` resolves the host first and refuses private, loopback, link-local
and reserved addresses. That includes `169.254.169.254`, the instance metadata
endpoint on AWS, GCP and Azure, which serves credentials to anything that can
reach it. Non-HTTP schemes (`file://`, `ftp://`, `gopher://`) are rejected
before any request is made.

## Adding a licensed provider

Subclass `EnrichmentProvider`, keep `terms_compliant = True`, and register it:

```python
from enrichment.base import EnrichmentProvider, EnrichmentResult
from enrichment.registry import register


@register
class ProxycurlProvider(EnrichmentProvider):
    name = "proxycurl"
    requires_credentials = True
    terms_compliant = True

    async def enrich_person(self, identifier, **context) -> EnrichmentResult: ...

    async def enrich_company(self, identifier, **context) -> EnrichmentResult: ...
```

Then add it to `ENRICHMENT_PROVIDERS`, which is an ordered list:

```bash
ENRICHMENT_PROVIDERS=manual,proxycurl,public_web
```

Options worth considering, each of which licenses the data it sells:

| Need | Options |
|---|---|
| Person and company profiles | Proxycurl, Apollo, Clearbit, People Data Labs |
| LinkedIn data, first-party | LinkedIn Marketing Developer Platform (partner approval required) |
| Company firmographics | Clearbit, Crunchbase API |
| Hiring signals | Greenhouse / Lever job board APIs (a company's own board), Coresignal |
| News | NewsAPI — already wired in `company_intelligence.py` |

## Sending mail

Not a data-sourcing question, but the same principle. Cold outreach is
regulated: CAN-SPAM in the US, GDPR Article 6(1)(f) plus PECR in the UK and EU,
CASL in Canada. At minimum you need a lawful basis, a real physical address in
the message, and a working unsubscribe path.

This project does not implement suppression lists, unsubscribe handling or
consent tracking. `EMAIL_SENDING_ENABLED` defaults to `false` for that reason —
delivery is opt-in, and the README lists the gap.

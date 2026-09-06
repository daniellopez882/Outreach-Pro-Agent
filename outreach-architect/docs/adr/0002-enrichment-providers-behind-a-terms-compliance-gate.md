# ADR 0002 — Enrichment providers behind a terms-compliance gate, with an SSRF guard

**Status:** accepted · **Date:** 2026-09-06 (records the decision made in PR #1)

## Context

Lead research was `linkedin_scraper.py`: a username/password login to
LinkedIn followed by profile fetches. It never worked — the login POST sent no
CSRF token, the client did not follow the post-login redirect, and a `TypeError`
in the success check was swallowed by a bare `except`, so `login()` could only
return `False` and the parser was fed LinkedIn's authentication wall as though
it were a profile. It was also a breach of the LinkedIn User Agreement (§8.2),
which the code acknowledged with a comment rather than a control.
`CompanyIntelligence.check_hiring_signals` scraped LinkedIn Jobs through a
`NameError` that made every lookup report "no data".

In the same code path, a lead-supplied `company_website` went straight to
`httpx.get`: a URL of `http://169.254.169.254/` would have read cloud instance
credentials (SSRF).

## Decision

1. Enrichment is an interface (`enrichment/base.py`), and providers are
   constructed only through `enrichment/registry.py`. Each provider class
   declares `terms_compliant`; the registry refuses to construct one flagged
   `False`, and `tests/` fail the build if that gate is removed.
2. Two compliant providers ship: `manual` (operator-supplied data) and
   `public_web`, which fetches only public pages, honours `robots.txt`,
   throttles per host, caps response size, and identifies itself truthfully
   in its `User-Agent` rather than impersonating a browser.
3. `public_web` resolves every host before connecting and refuses private,
   loopback, link-local and reserved addresses (`enrichment/public_web.py`),
   so no lead-controlled URL can reach the instance metadata service or the
   internal network.
4. The hiring-signals lookup returns `available: False` with a reason rather
   than a scraped or fabricated answer.
5. Adding a licensed data vendor is a subclass plus one entry in
   `ENRICHMENT_PROVIDERS` — [data-sourcing.md](../data-sourcing.md) walks
   through it.

## Consequences

- Less data than the scraper promised, and all of it obtained on terms the
  operator can defend. The README says so.
- The SSRF guard is DNS-based: a host that resolves to a public address at
  check time and a private one at connect time (rebinding) is a residual
  risk, noted in the threat model.
- A provider that cannot be constructed is a configuration error at startup,
  not a silent fallback.

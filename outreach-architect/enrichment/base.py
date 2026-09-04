"""
enrichment/base.py
The interface every lead-enrichment source implements.

Why this exists
---------------
Enrichment was previously a single concrete class, ``LinkedInScraper``, that
logged into LinkedIn with a username and password and scraped profile pages.
That had two problems.

**It did not work.** ``login()`` posted to ``/uas/login-submit`` with no CSRF
token, which LinkedIn rejects; ``httpx.Client`` does not follow redirects by
default, so the post-login redirect was never followed; and the success check
``'feed' in response.url`` raises ``TypeError: argument of type 'URL' is not a
container or iterable``, swallowed by a bare ``except Exception``. The method
could only ever return ``False``. Unauthenticated profile fetches then received
LinkedIn's authentication wall, which ``_parse_profile_html`` parsed as though
it were a profile.

**It should not work.** Automated login and scraping breach the LinkedIn User
Agreement (section 8.2), and credential-based automation gets accounts
terminated. The original code said as much in a comment -- "Use at your own
risk" -- which is not a control.

So enrichment is now an interface with swappable implementations. The shipped
defaults are compliant: operator-supplied data, and a public-web fetcher that
honours ``robots.txt``. A licensed vendor (the official LinkedIn Marketing API,
Apollo, Clearbit, Proxycurl) can be added as another provider without touching
the orchestrator. See ``docs/data-sourcing.md``.
"""

from __future__ import annotations

import abc
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


class ProviderUnavailable(RuntimeError):
    """Raised when a provider is selected but cannot run (missing credentials)."""


@dataclass
class EnrichmentResult:
    """
    What every provider returns.

    ``source`` and ``confidence`` are mandatory so downstream prompts can say
    where a fact came from. The previous scraper returned bare dicts that
    sometimes contained an ``error`` key instead of data, and callers had no
    reliable way to tell a successful enrichment from a failed one.
    """

    source: str
    subject: str
    data: dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0
    partial: bool = False
    errors: list[str] = field(default_factory=list)
    fetched_at: str = field(
        default_factory=lambda: datetime.now(UTC).isoformat().replace("+00:00", "Z")
    )

    @property
    def ok(self) -> bool:
        return not self.errors and bool(self.data)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "subject": self.subject,
            "data": self.data,
            "confidence": round(self.confidence, 3),
            "partial": self.partial,
            "errors": list(self.errors),
            "fetched_at": self.fetched_at,
            "ok": self.ok,
        }

    @classmethod
    def failed(cls, source: str, subject: str, reason: str) -> EnrichmentResult:
        return cls(source=source, subject=subject, errors=[reason], confidence=0.0)


class EnrichmentProvider(abc.ABC):
    """A source of information about a lead."""

    #: Short identifier used in configuration and logs.
    name: str = "base"

    #: Whether this provider needs credentials to function.
    requires_credentials: bool = False

    #: Set False for any provider whose terms of service forbid automated use.
    #: The registry refuses to construct a provider with this unset.
    terms_compliant: bool = True

    @abc.abstractmethod
    async def enrich_person(self, identifier: str, **context: Any) -> EnrichmentResult:
        """Return what is known about a person."""

    @abc.abstractmethod
    async def enrich_company(self, identifier: str, **context: Any) -> EnrichmentResult:
        """Return what is known about a company."""

    async def health(self) -> bool:
        """Whether this provider can currently serve requests."""
        return True

    def __repr__(self) -> str:
        return f"{type(self).__name__}(name={self.name!r})"

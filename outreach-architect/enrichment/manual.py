"""
enrichment/manual.py
Enrichment from data the operator already holds.

This is the default provider and the only one that needs no network access. A
lead imported from a CRM export, a conference list or a signup form already
carries most of what personalisation needs; fetching it again from a third
party adds legal exposure without adding much signal.
"""

from __future__ import annotations

from typing import Any

from enrichment.base import EnrichmentProvider, EnrichmentResult

# Fields that carry enough signal to personalise an opening line.
SIGNAL_FIELDS = (
    "name",
    "job_title",
    "company",
    "location",
    "industry",
    "company_size",
    "company_website",
    "notes",
    "tags",
    "source",
)


class ManualProvider(EnrichmentProvider):
    """Return the operator-supplied fields already attached to the lead."""

    name = "manual"
    requires_credentials = False
    terms_compliant = True

    async def enrich_person(self, identifier: str, **context: Any) -> EnrichmentResult:
        lead = context.get("lead") or {}
        data = {k: v for k, v in lead.items() if k in SIGNAL_FIELDS and v not in (None, "", [])}

        if not data:
            return EnrichmentResult.failed(
                self.name, identifier, "no operator-supplied fields present on the lead"
            )

        # Confidence scales with how much the operator actually knows. It is a
        # completeness measure, not an accuracy claim.
        confidence = min(1.0, len(data) / len(SIGNAL_FIELDS))
        return EnrichmentResult(
            source=self.name,
            subject=identifier,
            data=data,
            confidence=confidence,
            partial=confidence < 0.5,
        )

    async def enrich_company(self, identifier: str, **context: Any) -> EnrichmentResult:
        lead = context.get("lead") or {}
        data = {
            key: lead[key]
            for key in ("company", "company_website", "industry", "company_size")
            if lead.get(key)
        }
        if not data:
            return EnrichmentResult.failed(
                self.name, identifier, "no company fields present on the lead"
            )
        return EnrichmentResult(
            source=self.name,
            subject=identifier,
            data=data,
            confidence=min(1.0, len(data) / 4),
            partial=len(data) < 2,
        )

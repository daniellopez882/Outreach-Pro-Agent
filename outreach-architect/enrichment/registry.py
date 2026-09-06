"""
enrichment/registry.py
Provider lookup, with a compliance gate.

A provider whose ``terms_compliant`` flag is False cannot be constructed here.
That is deliberate: the previous LinkedIn scraper documented its own risk in a
comment ("Use at your own risk - LinkedIn may ban accounts for scraping"), and
a comment is not a control. The check makes adding a non-compliant source a
visible, explicit act rather than an import.
"""

from __future__ import annotations

from enrichment.base import EnrichmentProvider, ProviderUnavailable
from enrichment.manual import ManualProvider
from enrichment.public_web import PublicWebProvider

_REGISTRY: dict[str, type[EnrichmentProvider]] = {
    ManualProvider.name: ManualProvider,
    PublicWebProvider.name: PublicWebProvider,
}


def available_providers() -> list[str]:
    return sorted(_REGISTRY)


def register(provider_cls: type[EnrichmentProvider]) -> type[EnrichmentProvider]:
    """Register a provider. Used by third-party integrations."""
    if not provider_cls.terms_compliant:
        raise ValueError(
            f"{provider_cls.__name__} is flagged terms_compliant=False and will not be "
            "registered. Use a licensed data vendor; see docs/data-sourcing.md."
        )
    _REGISTRY[provider_cls.name] = provider_cls
    return provider_cls


def get_provider(name: str, **kwargs) -> EnrichmentProvider:
    """Construct a provider by name."""
    try:
        provider_cls = _REGISTRY[name]
    except KeyError:
        raise ProviderUnavailable(
            f"unknown enrichment provider {name!r}; available: {available_providers()}"
        ) from None

    if not provider_cls.terms_compliant:
        raise ProviderUnavailable(f"provider {name!r} is not terms-compliant and is disabled")
    return provider_cls(**kwargs)

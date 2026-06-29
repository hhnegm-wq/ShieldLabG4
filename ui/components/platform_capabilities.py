from __future__ import annotations

from dataclasses import dataclass

from components.navigation import page_href


@dataclass(frozen=True)
class PlatformCapabilitySpec:
    key: str
    title: str
    body: str
    href: str
    icon: str
    cta: str = "Open ->"


PLATFORM_CAPABILITIES: tuple[PlatformCapabilitySpec, ...] = (
    PlatformCapabilitySpec(
        key="security_controls",
        title="Security Controls",
        body="HMAC API auth, UI tiering, rate limits, and quota-aware runtime controls are treated as live platform behavior.",
        href=page_href("settings"),
        icon="S",
    ),
    PlatformCapabilitySpec(
        key="validation_gates",
        title="Validation Gates",
        body="Benchmark status, threshold coverage, provenance checks, and release-gate diagnosis are visible as operating signals.",
        href=page_href("benchmark_dashboard"),
        icon="V",
    ),
    PlatformCapabilitySpec(
        key="provenance_trail",
        title="Provenance Trail",
        body="Validation summaries and reproducibility manifests stay attached to result sets so exports remain auditable after delivery.",
        href=page_href("results_explorer"),
        icon="P",
    ),
    PlatformCapabilitySpec(
        key="methods_evidence",
        title="Methods Evidence",
        body="Physics methods, governing references, and manuscript-ready evidence packs remain inspectable from the product surface.",
        href=page_href("methods"),
        icon="M",
    ),
)
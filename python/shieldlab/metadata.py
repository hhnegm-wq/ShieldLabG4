"""Shared product and ownership metadata for ShieldLab G4."""
from __future__ import annotations

from datetime import datetime

PRODUCT_NAME = "ShieldLab G4"
PRODUCT_TAGLINE = "Validated Radiation Shielding Workspace"
PRODUCT_SUBTITLE = "Analytical shielding, managed workflows, and reproducible reporting"
HOME_HERO_KICKER = "Validated Shielding Workspace"
HOME_HERO_BODY = (
    "Analytical gamma-ray and neutron shielding workspace with a 150-material "
    "NIST compendium, 100-isotope library, reference-traceable methods, and reproducible PDF and Excel export."
)
LEGAL_DISCLAIMER = (
    "ShieldLab G4 is an analytical and simulation-support platform for research, "
    "screening, education, and engineering pre-assessment. It is not certified for "
    "clinical, regulatory, or safety-critical release decisions without independent "
    "verification, validation, and qualified expert review."
)
SUPPORT_SLA = "Support contact is provided directly through the platform ownership contacts listed below."
PLATFORM_SCOPE = (
    "The workspace combines study design, simulation workflow, analytical shielding, "
    "dose-rate tools, reference-traceable methods, and reproducible reporting in one managed shell."
)
COPYRIGHT_OWNER = "Dr. Hani H. Negm"
CONTACT_EMAILS = (
    "hhnegm@ju.edu.sa",
    "negm_sci@aun.edu.sa",
)
CONTACT_PHONE = "+966596301743"


def current_year() -> int:
    """Return the current UTC calendar year."""
    return datetime.utcnow().year


def support_contact_line() -> str:
    """Return a compact support/contact line for UI display."""
    return " | ".join([*CONTACT_EMAILS, CONTACT_PHONE])


def copyright_notice(year: int | None = None) -> str:
    """Return the canonical copyright notice."""
    return f"Copyright © {year or current_year()} {COPYRIGHT_OWNER}. All rights reserved."


def figure_footer_label(version: str = "") -> str:
    """Return a compact figure footer label."""
    version_part = f" v{version}" if version else ""
    return f"{PRODUCT_NAME}{version_part} · © {current_year()} {COPYRIGHT_OWNER}"


def platform_footer_text() -> str:
    """Return the standard platform footer text."""
    return (
        f"{copyright_notice()} "
        f"Contact: {support_contact_line()}"
    )


def ownership_lines() -> tuple[str, ...]:
    """Return ownership and contact lines for structured UI rendering."""
    return (COPYRIGHT_OWNER, *CONTACT_EMAILS, CONTACT_PHONE)
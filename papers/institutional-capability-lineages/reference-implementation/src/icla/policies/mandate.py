"""
Institutional Capability Lineages (ICLA)
Reference Implementation

Copyright (c) 2026 Mariano Garralda-Barrio

Licensed under the MIT License.
See the LICENSE file in the repository root for details.
"""

# Module purpose: Decide when an admitted operational mandate requires re-resolution.

from __future__ import annotations


def assess_reresolution(
    *,
    intent_materially_changed: bool = False,
    coverage_sufficient: bool = True,
    authority_valid: bool = True,
    sources_fresh: bool = True,
    risk_unchanged: bool = True,
    assurance_unchanged: bool = True,
) -> tuple[bool, tuple[str, ...]]:
    """Return whether the current assembly mandate is no longer sufficient."""

    conditions = (
        (intent_materially_changed, "intent-materially-changed"),
        (not coverage_sufficient, "coverage-insufficient"),
        (not authority_valid, "authority-invalid"),
        (not sources_fresh, "source-or-binding-stale"),
        (not risk_unchanged, "risk-changed"),
        (not assurance_unchanged, "assurance-changed"),
    )
    reasons = tuple(reason for triggered, reason in conditions if triggered)
    return bool(reasons), reasons

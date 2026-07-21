"""
Institutional Capability Lineages (ICLA)
Reference Implementation

Copyright (c) 2026 Mariano Garralda-Barrio

Licensed under the MIT License.
See the LICENSE file in the repository root for details.
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class AdmissibilityResult:
    admitted: bool
    checks: dict[str, bool]
    rationale: list[str] = field(default_factory=list)


def assess(
    *,
    coverage: bool,
    authority: bool,
    freshness: bool,
    assurance: bool,
    budget: bool,
    conflicts: bool,
) -> AdmissibilityResult:
    checks = {
        "coverage": coverage,
        "authority": authority,
        "freshness": freshness,
        "assurance": assurance,
        "budget": budget,
        "conflicts": conflicts,
    }
    failed = [name for name, passed in checks.items() if not passed]
    return AdmissibilityResult(
        not failed, checks, [] if not failed else [f"Failed: {', '.join(failed)}"]
    )

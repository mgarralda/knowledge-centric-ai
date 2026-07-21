"""
Institutional Capability Lineages (ICLA)
Reference Implementation

Copyright (c) 2026 Mariano Garralda-Barrio

Licensed under the MIT License.
See the LICENSE file in the repository root for details.
"""

_LEVELS = {"basic": 0, "standard": 1, "high": 2, "critical": 3}


def assurance_satisfies(offered: str, required: str) -> tuple[bool, str]:
    result = _LEVELS.get(offered, -1) >= _LEVELS.get(required, 99)
    return (
        result,
        f"offered assurance {offered!r} {'meets' if result else 'does not meet'} {required!r}",
    )

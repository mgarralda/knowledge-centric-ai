"""
Institutional Capability Lineages (ICLA)
Reference Implementation

Copyright (c) 2026 Mariano Garralda-Barrio

Licensed under the MIT License.
See the LICENSE file in the repository root for details.
"""

from datetime import UTC, datetime


def is_fresh(expires_at: str | None, *, now: datetime | None = None) -> tuple[bool, str]:
    if not expires_at:
        return True, "no expiry declared"
    expiry = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
    current = now or datetime.now(UTC)
    return (current <= expiry, "artifact is fresh" if current <= expiry else "artifact has expired")

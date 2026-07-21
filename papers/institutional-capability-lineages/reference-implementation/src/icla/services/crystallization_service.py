"""
Institutional Capability Lineages (ICLA)
Reference Implementation

Copyright (c) 2026 Mariano Garralda-Barrio

Licensed under the MIT License.
See the LICENSE file in the repository root for details.
"""

from collections import Counter
from uuid import NAMESPACE_URL, uuid5

from ..models.crystallization import CapabilityProposal


class CrystallizationService:
    def propose(
        self,
        signatures: list[str],
        *,
        proposed_name: str,
        responsibility: str,
        threshold: int = 3,
        candidate_owner: str | None = None,
    ) -> CapabilityProposal:
        counts = Counter(signatures)
        pattern, count = counts.most_common(1)[0] if counts else ("", 0)
        if count < threshold:
            raise ValueError(f"No recurrent pattern reaches threshold {threshold}")
        return CapabilityProposal(
            id=f"PROP-{str(uuid5(NAMESPACE_URL, proposed_name + pattern)).upper()}",
            recurrent_pattern_refs=[pattern] * count,
            proposed_name=proposed_name,
            responsibility=responsibility,
            candidate_owner=candidate_owner,
            overlap_analysis=["Requires governance review against the Registry"],
            score=count / len(signatures),
        )

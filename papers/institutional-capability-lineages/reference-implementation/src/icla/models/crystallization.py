"""
Institutional Capability Lineages (ICLA)
Reference Implementation

Copyright (c) 2026 Mariano Garralda-Barrio

Licensed under the MIT License.
See the LICENSE file in the repository root for details.
"""

# Module purpose: Governance input produced from recurrent assembly patterns.

from pydantic import Field

from .common import ExtensibleModel


class CapabilityProposal(ExtensibleModel):
    id: str
    recurrent_pattern_refs: list[str] = Field(min_length=1)
    proposed_name: str
    responsibility: str
    candidate_owner: str | None = None
    overlap_analysis: list[str] = Field(default_factory=list)
    draft_ckc_ref: str | None = None
    evidence_refs: list[str] = Field(default_factory=list)
    score: float | None = None

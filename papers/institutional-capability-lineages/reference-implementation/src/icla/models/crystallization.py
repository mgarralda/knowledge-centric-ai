"""
Institutional Capability Lineages (ICLA)
Reference Implementation

Copyright (c) 2026 Mariano Garralda-Barrio

Licensed under the MIT License.
See the LICENSE file in the repository root for details.
"""

# Module purpose: Governance input produced from recurrent assembly patterns.

from enum import StrEnum
from typing import Any

from pydantic import Field

from .common import ExtensibleModel


class ProposalStatus(StrEnum):
    PROPOSED = "proposed"
    UNDER_REVIEW = "under-review"
    APPROVED = "approved"
    REJECTED = "rejected"
    PROMOTED = "promoted"


class CapabilityProposal(ExtensibleModel):
    id: str
    status: ProposalStatus = ProposalStatus.PROPOSED
    recurrent_pattern_refs: list[str] = Field(min_length=1)
    proposed_name: str
    responsibility: str
    stable_assembly_rules: list[str] = Field(min_length=1)
    value_assessment: dict[str, Any]
    comparable_outcome_refs: list[str] = Field(min_length=1)
    candidate_owner: str
    overlap_analysis: list[str] = Field(min_length=1)
    draft_ckc_ref: str
    evidence_refs: list[str] = Field(default_factory=list)
    score: float | None = None
    lifecycle_history: list[dict[str, Any]] = Field(default_factory=list)
    assigned_identity: str | None = None
    initial_ckc_ref: str | None = None

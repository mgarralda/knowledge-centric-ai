"""
Institutional Capability Lineage Architecture (ICLA)
Reference Implementation

Copyright (c) 2026 Mariano Garralda-Barrio

Licensed under the MIT License.
See the LICENSE file in the repository root for details.
"""

# Module purpose: Pre-institutional capability proposals used by crystallization.

from enum import StrEnum
from typing import Any

from pydantic import Field, model_validator

from .common import SpecificationMetadata


class ProposalStatus(StrEnum):
    CANDIDATE = "candidate"
    SUBMITTED = "submitted"


class CapabilityProposal(SpecificationMetadata):
    """A candidate responsibility that has no institutional identity before promotion."""

    document_type: str = "capability-proposal"
    status: ProposalStatus
    proposed_responsibility: dict[str, Any]
    supporting_record_refs: list[str] = Field(min_length=1)
    recurrence_assessment: dict[str, Any]
    stable_assembly_rules: list[str] = Field(min_length=1)
    value_assessment: dict[str, Any]
    comparable_outcome_refs: list[str] = Field(min_length=1)
    candidate_owner: str
    overlap_analysis: list[dict[str, Any] | str] = Field(min_length=1)
    proposed_relations: list[dict[str, Any]] = Field(default_factory=list)
    proposal_scoped_ckc_draft_ref: str

    @model_validator(mode="after")
    def preserve_preinstitutional_boundary(self):
        forbidden = {"assigned_identity", "institutional_capability_id", "capability_ref"}
        if forbidden & self.model_dump().keys():
            raise ValueError("A pre-institutional proposal cannot carry capability identity")
        if self.proposal_scoped_ckc_draft_ref.startswith("CKC-"):
            raise ValueError("A proposal-scoped draft cannot anticipate an institutional CKC ID")
        provenance = self.generated_from.get("supporting_records", [])
        indexed_refs = {
            item.get("record_ref")
            for item in provenance
            if isinstance(item, dict) and item.get("record_ref")
        }
        if not set(self.supporting_record_refs).issubset(indexed_refs):
            raise ValueError("Supporting records must have resolvable provenance metadata")
        if (
            self.status == ProposalStatus.SUBMITTED
            and self.recurrence_assessment.get("justified_expectation") is not True
        ):
            raise ValueError(
                "A submitted proposal must justify expected recurrence or continuing "
                "institutional need"
            )
        return self

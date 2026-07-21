"""
Institutional Capability Lineages (ICLA)
Reference Implementation

Copyright (c) 2026 Mariano Garralda-Barrio

Licensed under the MIT License.
See the LICENSE file in the repository root for details.
"""

# Module purpose: Resolution, exclusion rationale, and admission decision.

from typing import Any

from pydantic import Field

from .common import ExtensibleModel, SpecificationMetadata


class CandidateCapability(ExtensibleModel):
    capability_id: str = Field(alias="capability")
    score: float = 0.0
    rationale: list[str] = Field(default_factory=list)


class ExcludedCapability(ExtensibleModel):
    capability_id: str = Field(alias="capability")
    reasons: list[str] = Field(default_factory=list)


class AdmittedCapability(ExtensibleModel):
    capability: str
    ckc: str
    version: int


class AdmissionDecision(ExtensibleModel):
    id: str
    status: str
    admitted_capabilities: list[AdmittedCapability] = Field(default_factory=list)
    rationale: list[str] = Field(default_factory=list)


class ResolutionResult(SpecificationMetadata):
    document_type: str = "capability-resolution"
    cee_ref: str
    intent_ref: str
    registry_snapshot_ref: str
    candidate_generation: dict[str, Any]
    relation_expansion: dict[str, Any]
    filtering: dict[str, Any]
    constraint_validation: list[dict[str, Any]]
    conflict_resolution: dict[str, Any]
    admission: AdmissionDecision
    trace: dict[str, Any]

    @property
    def selected_capabilities(self) -> list[str]:
        return [item.capability for item in self.admission.admitted_capabilities]

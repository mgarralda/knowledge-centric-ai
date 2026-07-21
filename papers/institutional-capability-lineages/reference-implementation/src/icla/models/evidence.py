"""
Institutional Capability Lineages (ICLA)
Reference Implementation

Copyright (c) 2026 Mariano Garralda-Barrio

Licensed under the MIT License.
See the LICENSE file in the repository root for details.
"""

# Module purpose: Execution evidence and gateway qualification receipts.

from typing import Any

from pydantic import Field

from .common import ExtensibleModel, SpecificationMetadata


class EvidenceReceipt(ExtensibleModel):
    id: str
    schema_conformity: bool | str
    metric_conformity: bool | str
    provenance_complete: bool
    qualification_status: str
    threshold_outcomes: list[dict[str, Any]] = Field(default_factory=list)
    rationale: list[str] = Field(default_factory=list)


class EvidenceBundle(SpecificationMetadata):
    document_type: str = "execution-evidence-bundle"
    status: str
    execution: dict[str, Any]
    lineage: dict[str, Any]
    results: dict[str, Any]
    artifacts: list[dict[str, Any]] = Field(min_length=1)
    measurements: dict[str, list[dict[str, Any]]]
    memory_record: dict[str, Any]
    candidate_knowledge: list[dict[str, Any]] = Field(default_factory=list)
    gateway_receipt: EvidenceReceipt | None = None

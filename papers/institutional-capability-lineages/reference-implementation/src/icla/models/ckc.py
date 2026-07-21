"""
Institutional Capability Lineages (ICLA)
Reference Implementation

Copyright (c) 2026 Mariano Garralda-Barrio

Licensed under the MIT License.
See the LICENSE file in the repository root for details.
"""

# Module purpose: Immutable Capability Knowledge Contract versions.

from typing import Any

from pydantic import Field

from .common import SpecificationMetadata


class CapabilityKnowledgeContract(SpecificationMetadata):
    document_type: str = "capability-knowledge-contract"
    capability_ref: str
    version: int = Field(ge=1)
    status: str
    predecessor: str | None = None
    knowledge_scope: dict[str, Any]
    obligations: list[dict[str, Any]] = Field(default_factory=list)
    authorities: dict[str, Any] = Field(default_factory=dict)
    evidence_contract: dict[str, Any]
    evaluation_contract: dict[str, Any]
    governance: dict[str, Any]
    projection_rules: dict[str, Any]
    source_bindings: list[dict[str, Any]] = Field(default_factory=list)

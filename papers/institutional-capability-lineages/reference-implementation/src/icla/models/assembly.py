"""
Institutional Capability Lineages (ICLA)
Reference Implementation

Copyright (c) 2026 Mariano Garralda-Barrio

Licensed under the MIT License.
See the LICENSE file in the repository root for details.
"""

# Module purpose: Immutable logical assembly and substrate-specific materializations.

from datetime import datetime
from typing import Any, Literal

from pydantic import Field

from .common import ExtensibleModel, SpecificationMetadata


class OperationalMandate(ExtensibleModel):
    authority_scope: Literal["execution-scoped"] = "execution-scoped"
    institutional_change_authority: Literal[False] = False
    local_autonomy: list[str] = Field(min_length=1)
    evidence_disclosure: Literal["evidence-contract-only"] = "evidence-contract-only"
    registry_interaction: Literal["reresolution-or-evidence-only"] = (
        "reresolution-or-evidence-only"
    )
    reresolution_triggers: list[str] = Field(min_length=1)


class Materialization(ExtensibleModel):
    id: str
    assembly_ref: str
    substrate: str
    uri: str | None = None
    content_hash: str
    created_at: datetime
    expires_at: datetime | None = None
    delivery_mode: Literal["bundle", "payload", "access-handles"] = "bundle"
    preserves_assembly_semantics: Literal[True] = True
    access_handles: list[dict[str, Any]] = Field(default_factory=list)


class Assembly(SpecificationMetadata):
    document_type: str = "contextual-assembly"
    status: str = "immutable"
    lineage: dict[str, Any]
    ckc_snapshot: list[dict[str, Any]] = Field(min_length=1)
    source_snapshot: list[dict[str, Any]] = Field(default_factory=list)
    policy_snapshot: list[dict[str, Any]] = Field(default_factory=list)
    transformation_snapshot: list[dict[str, Any]] = Field(default_factory=list)
    operational_mandate: OperationalMandate
    selection: dict[str, Any]
    evaluation_contract: dict[str, Any]
    evidence_contract: dict[str, Any]
    correctness: dict[str, bool]
    retention: dict[str, Any] = Field(default_factory=dict)
    access_policy_ref: str | None = None
    materializations: list[dict[str, Any]] = Field(default_factory=list)

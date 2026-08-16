"""
Institutional Capability Lineage Architecture (ICLA)
Reference Implementation

Copyright (c) 2026 Mariano Garralda-Barrio

Licensed under the MIT License.
See the LICENSE file in the repository root for details.
"""

# Module purpose: Separate immutable assembly and CEE-side materialization records.

from datetime import datetime
from typing import Any, Literal

from pydantic import Field, model_validator

from .common import ExtensibleModel, SpecificationMetadata


class OperationalMandate(ExtensibleModel):
    authority_scope: Literal["execution-scoped"] = "execution-scoped"
    institutional_change_authority: Literal[False] = False
    local_autonomy: list[str] = Field(min_length=1)
    evidence_disclosure: Literal["evidence-contract-only"] = "evidence-contract-only"
    registry_interaction: Literal["reresolution-or-evidence-only"] = "reresolution-or-evidence-only"
    reresolution_triggers: list[str] = Field(min_length=1)


class VersionedMaterializationComponent(ExtensibleModel):
    id: str
    version: int | str


class MaterializationRepresentation(ExtensibleModel):
    kind: Literal["bundle", "workspace", "message", "procedure", "payload", "access-handles"]
    control: Literal["cee-controlled"] = "cee-controlled"
    payload_retention: Literal["policy-dependent"] = "policy-dependent"
    local_reference: str | None = None


class MaterializationAccess(ExtensibleModel):
    mode: Literal["local-reference", "governed-access-handles"]
    policy_ref: str
    handles: list[dict[str, Any]] = Field(default_factory=list)


class Materialization(SpecificationMetadata):
    document_type: Literal["cee-side-materialization"] = "cee-side-materialization"
    status: Literal["immutable"] = "immutable"
    id: str
    assembly_ref: str
    cee_ref: str
    substrate: VersionedMaterializationComponent
    transformation: VersionedMaterializationComponent
    representation: MaterializationRepresentation
    content_hash: str
    created_at: datetime
    expires_at: datetime | None = None
    access: MaterializationAccess
    evaluation_binding: VersionedMaterializationComponent
    evidence_binding: VersionedMaterializationComponent
    preserves_assembly_semantics: Literal[True] = True
    preserves_assembly_authority: Literal[True] = True


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
    correctness_trace: dict[str, Any] = Field(default_factory=dict)
    retention: dict[str, Any] = Field(default_factory=dict)
    access_policy_ref: str | None = None

    @model_validator(mode="before")
    @classmethod
    def reject_retrospective_materializations(cls, value: Any) -> Any:
        if isinstance(value, dict) and "materializations" in value:
            raise ValueError("An immutable assembly cannot embed later materialization records")
        return value

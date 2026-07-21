"""
Institutional Capability Lineages (ICLA)
Reference Implementation

Copyright (c) 2026 Mariano Garralda-Barrio

Licensed under the MIT License.
See the LICENSE file in the repository root for details.
"""

# Module purpose: Immutable logical assembly and substrate-specific materializations.

from datetime import datetime
from typing import Any

from pydantic import Field

from .common import ExtensibleModel, SpecificationMetadata


class Materialization(ExtensibleModel):
    id: str
    assembly_ref: str
    substrate: str
    uri: str | None = None
    content_hash: str
    created_at: datetime
    expires_at: datetime | None = None


class Assembly(SpecificationMetadata):
    document_type: str = "contextual-assembly"
    status: str = "immutable"
    lineage: dict[str, Any]
    ckc_snapshot: list[dict[str, Any]] = Field(min_length=1)
    source_snapshot: list[dict[str, Any]] = Field(default_factory=list)
    policy_snapshot: list[dict[str, Any]] = Field(default_factory=list)
    transformation_snapshot: list[dict[str, Any]] = Field(default_factory=list)
    selection: dict[str, Any]
    evaluation_contract: dict[str, Any]
    evidence_contract: dict[str, Any]
    correctness: dict[str, bool]
    retention: dict[str, Any] = Field(default_factory=dict)
    access_policy_ref: str | None = None
    materializations: list[dict[str, Any]] = Field(default_factory=list)

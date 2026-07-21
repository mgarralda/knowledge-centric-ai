"""
Institutional Capability Lineages (ICLA)
Reference Implementation

Copyright (c) 2026 Mariano Garralda-Barrio

Licensed under the MIT License.
See the LICENSE file in the repository root for details.
"""

# Module purpose: Shared value objects and artifact metadata.

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


def utc_now() -> datetime:
    return datetime.now(UTC)


class ExtensibleModel(BaseModel):
    """Schema-aligned base class that preserves specification extensions."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)


class LifecycleStatus(StrEnum):
    DISCOVERED = "discovered"
    PROPOSED = "proposed"
    CANONICAL = "canonical"
    ACTIVE = "active"
    UNDER_REVIEW = "under-review"
    RETIRED = "retired"
    MERGED = "merged"


class RiskLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AssuranceLevel(StrEnum):
    BASIC = "basic"
    STANDARD = "standard"
    HIGH = "high"


class KnowledgeRole(StrEnum):
    """Overlapping functional roles of governed organizational knowledge."""

    SEMANTIC = "semantic"
    PROCEDURAL = "procedural"
    EPISODIC = "episodic"


class SpecificationMetadata(ExtensibleModel):
    document_type: str
    format_version: str = "icla-artifact/0.1-draft"
    specification_version: dict[str, str] = Field(default_factory=lambda: {"icla-spec": "0.1.0"})
    id: str
    artifact_status: str = "reference"
    normative: bool = False
    schema_ref: str | None = None
    generated_from: dict[str, Any] = Field(default_factory=dict)


class TypedRelation(ExtensibleModel):
    relation_type: str = Field(alias="type")
    source: str = Field(alias="from")
    target: str = Field(alias="to")

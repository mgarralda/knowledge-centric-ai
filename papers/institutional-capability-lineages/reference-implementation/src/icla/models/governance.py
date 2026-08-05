"""
Institutional Capability Lineage Architecture (ICLA)
Reference Implementation

Copyright (c) 2026 Mariano Garralda-Barrio

Licensed under the MIT License.
See the LICENSE file in the repository root for details.
"""

# Module purpose: Declared governance decisions and separate activation records.

from datetime import datetime
from typing import Any, Literal

from pydantic import Field

from .common import ExtensibleModel, SpecificationMetadata


class GovernanceDecision(SpecificationMetadata):
    document_type: str = "governance-decision"
    status: str
    inputs: dict[str, Any]
    review: dict[str, Any]
    dispositions: dict[str, Any]
    impact_record: dict[str, Any]
    successor_delta: dict[str, Any] = Field(default_factory=dict)
    successor_append: dict[str, Any] = Field(default_factory=dict)
    activation: dict[str, Any] = Field(default_factory=dict)
    historical_immutability: dict[str, Any] = Field(default_factory=dict)
    capability_formation: dict[str, Any]
    resulting_lineage_edges: list[dict[str, Any]] = Field(min_length=1)


class ActivationRecord(ExtensibleModel):
    id: str
    decision_ref: str
    capability_ref: str
    successor_append_ref: str
    previous_ckc: dict[str, Any]
    active_ckc: dict[str, Any]
    rollback_target: dict[str, Any]
    action: str = "activate"
    activated_by: str
    activated_at: datetime


class SuccessorAppendReceipt(ExtensibleModel):
    id: str
    decision_ref: str
    capability_ref: str
    predecessor_ref: str
    successor_ref: str
    delta_ref: str
    lineage_size: int = Field(ge=2)
    status: Literal["inactive-successor"] = "inactive-successor"
    appended_by: str
    appended_at: datetime

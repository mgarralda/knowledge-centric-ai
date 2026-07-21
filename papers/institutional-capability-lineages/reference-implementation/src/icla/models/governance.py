"""
Institutional Capability Lineages (ICLA)
Reference Implementation

Copyright (c) 2026 Mariano Garralda-Barrio

Licensed under the MIT License.
See the LICENSE file in the repository root for details.
"""

# Module purpose: Declared governance decisions and separate activation records.

from datetime import datetime
from typing import Any

from pydantic import Field

from .common import ExtensibleModel, SpecificationMetadata


class GovernanceDecision(SpecificationMetadata):
    document_type: str = "governance-decision"
    status: str
    inputs: dict[str, Any]
    review: dict[str, Any]
    dispositions: dict[str, Any]
    impact_record: dict[str, Any]
    activation: dict[str, Any]
    historical_immutability: dict[str, Any]
    capability_formation: dict[str, Any]
    resulting_lineage_edges: list[dict[str, Any]] = Field(min_length=1)


class ActivationRecord(ExtensibleModel):
    id: str
    decision_ref: str
    capability_ref: str
    previous_ckc: dict[str, Any]
    active_ckc: dict[str, Any]
    activated_by: str
    activated_at: datetime

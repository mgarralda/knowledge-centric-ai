"""
Institutional Capability Lineage Architecture (ICLA)
Reference Implementation

Copyright (c) 2026 Mariano Garralda-Barrio

Licensed under the MIT License.
See the LICENSE file in the repository root for details.
"""

# Module purpose: Operational intent supplied to capability resolution.

from typing import Any, Literal

from pydantic import Field

from .common import ExtensibleModel, SpecificationMetadata


class CEEConfiguration(ExtensibleModel):
    id: str
    resolution: dict[str, Any]
    authorization: dict[str, Any]
    assurance: dict[str, Any]
    traceability: dict[str, Any]
    evidence_interpretation: dict[str, Any]


class CEEBoundary(ExtensibleModel):
    id: str
    boundary_scope: Literal["execution-scoped"] = "execution-scoped"
    type: str
    configuration: CEEConfiguration


class Intent(SpecificationMetadata):
    document_type: str = "operational-intent"
    goal: str
    context: dict[str, Any]
    cee: CEEBoundary
    consumer: dict[str, Any]
    risk: dict[str, Any]
    budget: dict[str, Any]
    assurance: dict[str, Any]
    required_outcomes: list[str] = Field(min_length=1)

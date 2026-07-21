"""
Institutional Capability Lineages (ICLA)
Reference Implementation

Copyright (c) 2026 Mariano Garralda-Barrio

Licensed under the MIT License.
See the LICENSE file in the repository root for details.
"""

# Module purpose: Operational intent supplied to capability resolution.

from typing import Any

from pydantic import Field

from .common import SpecificationMetadata


class Intent(SpecificationMetadata):
    document_type: str = "operational-intent"
    goal: str
    context: dict[str, Any]
    cee: dict[str, Any]
    consumer: dict[str, Any]
    risk: dict[str, Any]
    budget: dict[str, Any]
    assurance: dict[str, Any]
    required_outcomes: list[str] = Field(min_length=1)

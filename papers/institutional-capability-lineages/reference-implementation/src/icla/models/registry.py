"""
Institutional Capability Lineages (ICLA)
Reference Implementation

Copyright (c) 2026 Mariano Garralda-Barrio

Licensed under the MIT License.
See the LICENSE file in the repository root for details.
"""

# Module purpose: Immutable Registry snapshots and typed relations.

from datetime import datetime
from typing import Any

from pydantic import Field

from .capability import Capability
from .common import SpecificationMetadata, TypedRelation


class RegistryRelation(TypedRelation):
    pass


class RegistrySnapshot(SpecificationMetadata):
    document_type: str = "institutional-capability-registry-snapshot"
    registry: dict[str, Any]
    capabilities: list[Capability] = Field(min_length=1)
    relations: list[RegistryRelation] = Field(default_factory=list)
    created_at: datetime | None = None

    def capability(self, capability_id: str) -> Capability | None:
        return next((item for item in self.capabilities if item.id == capability_id), None)

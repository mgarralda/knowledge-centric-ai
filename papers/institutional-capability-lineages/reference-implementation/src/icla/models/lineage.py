"""
Institutional Capability Lineages (ICLA)
Reference Implementation

Copyright (c) 2026 Mariano Garralda-Barrio

Licensed under the MIT License.
See the LICENSE file in the repository root for details.
"""

# Module purpose: Typed, connected institutional capability lineage graph.

from pydantic import Field

from .common import ExtensibleModel


class LineageNode(ExtensibleModel):
    id: str
    node_type: str
    artifact_ref: str


class LineageEdge(ExtensibleModel):
    source: str = Field(alias="from")
    relation_type: str = Field(alias="type")
    target: str = Field(alias="to")


class InstitutionalCapabilityLineage(ExtensibleModel):
    capability_id: str
    nodes: list[LineageNode] = Field(default_factory=list)
    edges: list[LineageEdge] = Field(default_factory=list)

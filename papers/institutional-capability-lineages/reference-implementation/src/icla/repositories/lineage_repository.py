"""
Institutional Capability Lineages (ICLA)
Reference Implementation

Copyright (c) 2026 Mariano Garralda-Barrio

Licensed under the MIT License.
See the LICENSE file in the repository root for details.
"""

from ..exceptions import LineageError
from ..models.lineage import InstitutionalCapabilityLineage, LineageEdge, LineageNode
from ..storage import AppendOnlyStore


class LineageRepository:
    def __init__(self, store: AppendOnlyStore) -> None:
        self.store = store

    def append_node(self, capability_id: str, node: LineageNode) -> None:
        value = node.model_dump(mode="json", by_alias=True)
        value["capability_id"] = capability_id
        self.store.append("lineage-nodes", f"{capability_id}-{node.id}", value)

    def append_edge(self, capability_id: str, edge: LineageEdge) -> None:
        key = f"{capability_id}-{edge.source}-{edge.relation_type}-{edge.target}"
        value = edge.model_dump(mode="json", by_alias=True)
        value["capability_id"] = capability_id
        self.store.append("lineage-edges", key, value)

    def get_capability_lineage(self, capability_id: str) -> InstitutionalCapabilityLineage:
        nodes = [
            LineageNode.model_validate(item)
            for item in self.store.list("lineage-nodes")
            if item.get("capability_id") == capability_id
        ]
        ids = {node.id for node in nodes}
        edges = [
            LineageEdge.model_validate(item)
            for item in self.store.list("lineage-edges")
            if item.get("capability_id") == capability_id
            and (item.get("from") in ids or item.get("to") in ids)
        ]
        return InstitutionalCapabilityLineage(capability_id=capability_id, nodes=nodes, edges=edges)

    @staticmethod
    def validate_connected_trace(lineage: InstitutionalCapabilityLineage) -> None:
        if len(lineage.nodes) < 2:
            return
        adjacency = {node.id: set() for node in lineage.nodes}
        for edge in lineage.edges:
            if edge.source in adjacency and edge.target in adjacency:
                adjacency[edge.source].add(edge.target)
                adjacency[edge.target].add(edge.source)
        seen, pending = set(), [lineage.nodes[0].id]
        while pending:
            current = pending.pop()
            if current not in seen:
                seen.add(current)
                pending.extend(adjacency[current] - seen)
        if seen != set(adjacency):
            raise LineageError(f"Disconnected lineage nodes: {sorted(set(adjacency) - seen)}")

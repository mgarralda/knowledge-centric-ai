"""
Institutional Capability Lineages (ICLA)
Reference Implementation

Copyright (c) 2026 Mariano Garralda-Barrio

Licensed under the MIT License.
See the LICENSE file in the repository root for details.
"""

# Module purpose: Read-only Registry navigation and filtering.

from collections import deque

from ..models.registry import RegistrySnapshot


class RegistryService:
    def __init__(self, snapshot: RegistrySnapshot) -> None:
        self.snapshot = snapshot

    def get_capability(self, capability_id: str):
        return self.snapshot.capability(capability_id)

    def filter(
        self,
        *,
        domain: str | None = None,
        lifecycle: str | None = None,
        owner: str | None = None,
        policy_ref: str | None = None,
        conditions: dict[str, str] | None = None,
    ):
        required_conditions = conditions or {}
        return [
            item
            for item in self.snapshot.capabilities
            if (domain is None or item.domain == domain)
            and (lifecycle is None or item.lifecycle == lifecycle)
            and (owner is None or item.owner == owner)
            and (policy_ref is None or policy_ref in item.policy_refs)
            and all(item.conditions.get(key) == value for key, value in required_conditions.items())
        ]

    def relations_from(self, capability_id: str, *, relation_types: set[str] | None = None):
        return [
            relation
            for relation in self.snapshot.relations
            if relation.source == capability_id
            and (relation_types is None or relation.relation_type in relation_types)
        ]

    def related(
        self,
        capability_id: str,
        *,
        max_depth: int = 1,
        relation_types: set[str] | None = None,
    ):
        visited, pending = {capability_id}, deque([(capability_id, 0)])
        traversed = []
        while pending:
            current, depth = pending.popleft()
            if depth >= max_depth:
                continue
            for relation in self.relations_from(current, relation_types=relation_types):
                if relation.target not in visited:
                    visited.add(relation.target)
                    traversed.append(relation)
                    pending.append((relation.target, depth + 1))
        return [
            self.snapshot.capability(item)
            for item in visited
            if item != capability_id and self.snapshot.capability(item)
        ], traversed

    def active_ckc_lookup(self, capability_id: str) -> tuple[str, int] | None:
        capability = self.get_capability(capability_id)
        return (
            None
            if capability is None
            else (capability.active_ckc.id, capability.active_ckc.version)
        )

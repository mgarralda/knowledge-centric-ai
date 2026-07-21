"""
Institutional Capability Lineages (ICLA)
Reference Implementation

Copyright (c) 2026 Mariano Garralda-Barrio

Licensed under the MIT License.
See the LICENSE file in the repository root for details.
"""

# Module purpose: Immutable CKC version repository; intentionally has no update operation.

from ..exceptions import ArtifactNotFoundError
from ..models.ckc import CapabilityKnowledgeContract
from ..storage import AppendOnlyStore


class CKCRepository:
    def __init__(self, store: AppendOnlyStore) -> None:
        self.store = store

    @staticmethod
    def _key(ckc_id: str, version: int) -> str:
        return f"{ckc_id}-v{version}"

    def get_version(self, ckc_id: str, version: int) -> CapabilityKnowledgeContract:
        return CapabilityKnowledgeContract.model_validate(
            self.store.read("ckcs", self._key(ckc_id, version))
        )

    def get_active_version(self, snapshot, capability_id: str) -> CapabilityKnowledgeContract:
        capability = snapshot.capability(capability_id)
        if capability is None:
            raise ArtifactNotFoundError(f"Capability not found: {capability_id}")
        return self.get_version(capability.active_ckc.id, capability.active_ckc.version)

    def append_successor(self, ckc: CapabilityKnowledgeContract) -> None:
        if ckc.version > 1 and not ckc.predecessor:
            raise ValueError("A successor CKC must declare its predecessor")
        self.store.append(
            "ckcs",
            self._key(ckc.id, ckc.version),
            ckc.model_dump(mode="json", by_alias=True, exclude_none=True),
        )

    def list_lineage(self, ckc_id: str) -> list[CapabilityKnowledgeContract]:
        return sorted(
            (
                CapabilityKnowledgeContract.model_validate(item)
                for item in self.store.list("ckcs")
                if item.get("id") == ckc_id
            ),
            key=lambda item: item.version,
        )

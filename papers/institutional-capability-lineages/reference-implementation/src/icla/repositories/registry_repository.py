"""
Institutional Capability Lineages (ICLA)
Reference Implementation

Copyright (c) 2026 Mariano Garralda-Barrio

Licensed under the MIT License.
See the LICENSE file in the repository root for details.
"""

# Module purpose: Registry persistence; active-pointer mutation requires an approved decision.

from ..exceptions import ActivationError, ArtifactNotFoundError
from ..models.registry import RegistrySnapshot
from ..storage import SnapshotStore, YamlStore


class RegistryRepository:
    def __init__(self, store: YamlStore) -> None:
        self.store = store

    def get_snapshot(self, snapshot_id: str) -> RegistrySnapshot:
        return RegistrySnapshot.model_validate(self.store.read("registry-snapshots", snapshot_id))

    def save_snapshot(self, snapshot: RegistrySnapshot) -> None:
        target = self.store
        data = snapshot.model_dump(mode="json", by_alias=True, exclude_none=True)
        if isinstance(target, SnapshotStore):
            target.append("registry-snapshots", snapshot.id, data)
        else:
            target.write("registry-snapshots", snapshot.id, data)

    def get_capability(self, snapshot_id: str, capability_id: str):
        capability = self.get_snapshot(snapshot_id).capability(capability_id)
        if capability is None:
            raise ArtifactNotFoundError(f"Capability not found: {capability_id}")
        return capability

    def list_capabilities(self, snapshot_id: str):
        return self.get_snapshot(snapshot_id).capabilities

    def update_active_pointer(
        self,
        snapshot: RegistrySnapshot,
        capability_id: str,
        *,
        ckc_id: str,
        version: int,
        decision_status: str,
    ) -> RegistrySnapshot:
        if decision_status != "approved":
            raise ActivationError("An approved governance decision is required")
        copy = snapshot.model_copy(deep=True)
        capability = copy.capability(capability_id)
        if capability is None:
            raise ArtifactNotFoundError(f"Capability not found: {capability_id}")
        capability.active_ckc.id = ckc_id
        capability.active_ckc.version = version
        return copy

"""
Institutional Capability Lineage Architecture (ICLA)
Reference Implementation

Copyright (c) 2026 Mariano Garralda-Barrio

Licensed under the MIT License.
See the LICENSE file in the repository root for details.
"""

# Module purpose: Immutable CKC version repository; intentionally has no update operation.

from ..exceptions import ArtifactNotFoundError
from ..models.ckc import CapabilityKnowledgeContract
from ..models.governance import FormationAppendReceipt, SuccessorAppendReceipt
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
        if ckc.version <= 1 or not ckc.predecessor:
            raise ValueError("A successor CKC must declare its predecessor")
        self._append_ckc(ckc)

    def append_initial(self, ckc: CapabilityKnowledgeContract) -> None:
        if ckc.version != 1 or ckc.predecessor:
            raise ValueError("An initial CKC must be version 1 without a predecessor")
        self._append_ckc(ckc)

    def _append_ckc(self, ckc: CapabilityKnowledgeContract) -> None:
        self.store.append(
            "ckcs",
            self._key(ckc.id, ckc.version),
            ckc.model_dump(mode="json", by_alias=True, exclude_none=True),
        )

    def get_latest_governed_version(self, ckc_id: str) -> CapabilityKnowledgeContract:
        lineage = self.list_lineage(ckc_id)
        if not lineage:
            raise ArtifactNotFoundError(f"CKC lineage not found: {ckc_id}")
        return lineage[-1]

    def record_append_receipt(self, receipt: SuccessorAppendReceipt) -> None:
        self.store.append(
            "successor-append-receipts",
            receipt.id,
            receipt.model_dump(mode="json", by_alias=True, exclude_none=True),
        )

    def get_append_receipt(self, ckc_id: str, version: int) -> SuccessorAppendReceipt:
        successor_ref = f"{ckc_id}@{version}"
        for item in self.store.list("successor-append-receipts"):
            if item.get("successor_ref") in {
                successor_ref,
                f"{ckc_id}-v{version}",
            }:
                return SuccessorAppendReceipt.model_validate(item)
        raise ArtifactNotFoundError(f"Successor has not been appended: {ckc_id}@{version}")

    def record_formation_receipt(self, receipt: FormationAppendReceipt) -> None:
        self.store.append(
            "formation-append-receipts",
            receipt.id,
            receipt.model_dump(mode="json", by_alias=True, exclude_none=True),
        )

    def get_formation_receipt(self, ckc_id: str, version: int) -> FormationAppendReceipt:
        initial_ref = f"{ckc_id}@{version}"
        for item in self.store.list("formation-append-receipts"):
            if item.get("initial_ckc_ref") in {initial_ref, f"{ckc_id}-v{version}"}:
                return FormationAppendReceipt.model_validate(item)
        raise ArtifactNotFoundError(f"Initial CKC has not been formed: {ckc_id}@{version}")

    def can_append_formation(self, ckc: CapabilityKnowledgeContract, receipt_id: str) -> bool:
        """Single-process preflight used to avoid partial writes on invalid requests."""
        return not self.store.path_for("ckcs", self._key(ckc.id, ckc.version)).exists() and not (
            self.store.path_for("formation-append-receipts", receipt_id).exists()
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

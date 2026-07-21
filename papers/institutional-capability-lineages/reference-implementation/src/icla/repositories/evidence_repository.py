"""
Institutional Capability Lineages (ICLA)
Reference Implementation

Copyright (c) 2026 Mariano Garralda-Barrio

Licensed under the MIT License.
See the LICENSE file in the repository root for details.
"""

from ..models.evidence import EvidenceBundle, EvidenceReceipt
from ..storage import AppendOnlyStore


class EvidenceRepository:
    def __init__(self, store: AppendOnlyStore) -> None:
        self.store = store

    def append(self, bundle: EvidenceBundle) -> None:
        self.store.append(
            "evidence", bundle.id, bundle.model_dump(mode="json", by_alias=True, exclude_none=True)
        )

    def get(self, evidence_id: str) -> EvidenceBundle:
        return EvidenceBundle.model_validate(self.store.read("evidence", evidence_id))

    def append_receipt(self, receipt: EvidenceReceipt) -> None:
        self.store.append(
            "evidence-receipts",
            receipt.id,
            receipt.model_dump(mode="json", by_alias=True, exclude_none=True),
        )

    def get_receipt(self, receipt_id: str) -> EvidenceReceipt:
        return EvidenceReceipt.model_validate(self.store.read("evidence-receipts", receipt_id))

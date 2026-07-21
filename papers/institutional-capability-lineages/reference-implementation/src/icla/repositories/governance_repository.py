"""
Institutional Capability Lineages (ICLA)
Reference Implementation

Copyright (c) 2026 Mariano Garralda-Barrio

Licensed under the MIT License.
See the LICENSE file in the repository root for details.
"""

from ..models.governance import ActivationRecord, GovernanceDecision
from ..storage import AppendOnlyStore


class GovernanceRepository:
    def __init__(self, store: AppendOnlyStore) -> None:
        self.store = store

    def append_decision(self, decision: GovernanceDecision) -> None:
        self.store.append(
            "decisions",
            decision.id,
            decision.model_dump(mode="json", by_alias=True, exclude_none=True),
        )

    def get_decision(self, decision_id: str) -> GovernanceDecision:
        return GovernanceDecision.model_validate(self.store.read("decisions", decision_id))

    def append_activation(self, record: ActivationRecord) -> None:
        self.store.append("activations", record.id, record.model_dump(mode="json", by_alias=True))

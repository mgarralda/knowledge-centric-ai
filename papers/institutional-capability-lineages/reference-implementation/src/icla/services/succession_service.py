"""
Institutional Capability Lineage Architecture (ICLA)
Reference Implementation

Copyright (c) 2026 Mariano Garralda-Barrio

Licensed under the MIT License.
See the LICENSE file in the repository root for details.
"""

# Module purpose: Append an authorized complete successor without activating it.

from ..exceptions import ArtifactNotFoundError, SuccessionError
from ..models.capability import Capability
from ..models.ckc import CapabilityKnowledgeContract
from ..models.common import utc_now
from ..models.governance import GovernanceDecision, SuccessorAppendReceipt
from ..repositories.ckc_repository import CKCRepository


def _refs(ckc: CapabilityKnowledgeContract) -> set[str]:
    return {f"{ckc.id}@{ckc.version}", f"{ckc.id}-v{ckc.version}"}


class SuccessionService:
    def __init__(self, repository: CKCRepository) -> None:
        self.repository = repository

    def append_successor(
        self,
        capability: Capability,
        predecessor: CapabilityKnowledgeContract,
        successor: CapabilityKnowledgeContract,
        decision: GovernanceDecision,
        *,
        actor: str,
    ) -> SuccessorAppendReceipt:
        if decision.status != "approved":
            raise SuccessionError("Successor append requires an approved governance decision")
        if not (
            capability.id == predecessor.capability_ref == successor.capability_ref
            and predecessor.id == successor.id
        ):
            raise SuccessionError("Capability, predecessor, and successor do not share identity")
        if successor.version != predecessor.version + 1:
            raise SuccessionError("A successor must immediately follow its predecessor")

        try:
            stored_predecessor = self.repository.get_version(predecessor.id, predecessor.version)
            latest = self.repository.get_latest_governed_version(predecessor.id)
        except ArtifactNotFoundError as error:
            raise SuccessionError(
                "The predecessor must already belong to the CKC lineage"
            ) from error
        if stored_predecessor != predecessor:
            raise SuccessionError("The predecessor does not match the retained CKC version")
        if latest.version != predecessor.version:
            raise SuccessionError(
                "stale-predecessor: predecessor is not the latest appended CKC"
            )

        authorized_actor = (
            successor.governance.get("succession_authority")
            or successor.governance.get("admission_authority")
            or capability.owner
        )
        if actor != authorized_actor:
            raise SuccessionError(
                f"Actor {actor!r} is not the declared succession authority {authorized_actor!r}"
            )

        predecessor_refs = _refs(predecessor)
        successor_refs = _refs(successor)
        authorizing_decision = successor.generated_from.get(
            "governance_decision"
        ) or successor.governance.get("admission_decision_ref")
        successor_delta_ref = successor.generated_from.get(
            "successor_delta"
        ) or successor.governance.get("successor_delta_ref")
        declared_predecessors = {
            successor.predecessor,
            successor.generated_from.get("predecessor"),
        }
        delta = decision.successor_delta
        required_evidence_refs = {
            decision.inputs.get("evidence_ref"),
            decision.inputs.get("qualification_receipt_ref"),
        } - {None, ""}
        if (
            authorizing_decision != decision.id
            or not predecessor_refs & declared_predecessors
            or delta.get("predecessor_ref") not in predecessor_refs
            or delta.get("successor_ref") not in successor_refs
            or delta.get("authorization_decision_ref") != decision.id
            or delta.get("rollback_ref") not in predecessor_refs
            or delta.get("successor_complete") is not True
            or delta.get("reconstruction_patch") is not False
            or not delta.get("changed_commitments")
            or not delta.get("rationale")
            or not delta.get("supporting_evidence_refs")
            or not required_evidence_refs.issubset(set(delta.get("supporting_evidence_refs", [])))
            or successor_delta_ref != delta.get("id")
        ):
            raise SuccessionError("Decision does not authorize this complete successor and delta")

        append = decision.successor_append
        expected_receipt_id = append.get("id") or (
            f"APPEND-{successor.capability_ref}-{successor.version:03d}"
        )
        if append and (
            append.get("capability") != capability.id
            or append.get("predecessor_ref") not in predecessor_refs
            or append.get("successor_ref") not in successor_refs
            or append.get("delta_ref") != delta.get("id")
            or append.get("authorization_decision_ref") != decision.id
        ):
            raise SuccessionError(
                "Declared successor append does not match the authorized transition"
            )

        self.repository.append_successor(successor)
        lineage = self.repository.list_lineage(successor.id)
        receipt = SuccessorAppendReceipt(
            id=str(expected_receipt_id),
            decision_ref=decision.id,
            capability_ref=capability.id,
            predecessor_ref=f"{predecessor.id}@{predecessor.version}",
            successor_ref=f"{successor.id}@{successor.version}",
            delta_ref=str(delta["id"]),
            lineage_size=len(lineage),
            appended_by=actor,
            appended_at=utc_now(),
        )
        self.repository.record_append_receipt(receipt)
        return receipt

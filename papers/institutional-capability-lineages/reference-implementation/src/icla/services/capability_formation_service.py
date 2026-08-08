"""
Institutional Capability Lineage Architecture (ICLA)
Reference Implementation

Copyright (c) 2026 Mariano Garralda-Barrio

Licensed under the MIT License.
See the LICENSE file in the repository root for details.
"""

# Module purpose: Governed identity assignment and initial-CKC append for crystallization.

from typing import Any

from ..exceptions import FormationError
from ..models.capability import Capability
from ..models.ckc import CapabilityKnowledgeContract
from ..models.common import LifecycleStatus, utc_now
from ..models.governance import FormationAppendReceipt, GovernanceDecision
from ..models.proposal import CapabilityProposal, ProposalStatus
from ..models.registry import RegistrySnapshot
from ..repositories.ckc_repository import CKCRepository


def _ckc_refs(ckc: CapabilityKnowledgeContract) -> set[str]:
    return {f"{ckc.id}@{ckc.version}", f"{ckc.id}-v{ckc.version}"}


def _affirmed(value: Any) -> bool:
    return value is True or str(value).casefold() in {"approved", "pass", "passed", "confirmed"}


class CapabilityFormationService:
    """Execute the deterministic part of Eq. (14), not proposal discovery or review."""

    def __init__(self, repository: CKCRepository) -> None:
        self.repository = repository

    def promote(
        self,
        snapshot: RegistrySnapshot,
        proposal: CapabilityProposal,
        initial_ckc: CapabilityKnowledgeContract,
        decision: GovernanceDecision,
        *,
        actor: str,
    ) -> tuple[RegistrySnapshot, FormationAppendReceipt]:
        formation = decision.capability_formation
        promotion = formation.get("governed_promotion", {})
        append = formation.get("formation_append", {})
        assigned = promotion.get("assigned_capability", {})

        if proposal.status != ProposalStatus.SUBMITTED:
            raise FormationError("Promotion requires a submitted proposal")
        if proposal.recurrence_assessment.get("established") is not True:
            raise FormationError("Promotion requires established recurrence")
        if decision.status != "approved":
            raise FormationError("Promotion requires an approved capability-formation decision")
        if formation.get("new_capability_created_by_this_decision") is not True:
            raise FormationError("Decision does not authorize a new institutional capability")
        if (
            promotion.get("proposal_ref") != proposal.id
            or promotion.get("review_decision_ref") != decision.id
        ):
            raise FormationError("Promotion does not reference its submitted proposal and decision")

        review = decision.review
        required_reviews = (
            "ownership_review",
            "distinctiveness_review",
            "overlap_review",
            "value_review",
            "evidence_review",
        )
        if not review.get("authority") or any(
            not _affirmed(review.get(field)) for field in required_reviews
        ):
            raise FormationError("Capability formation lacks the required governed review")
        authorized_actor = promotion.get("formation_authority") or review.get("authority")
        if actor != authorized_actor:
            raise FormationError(
                f"Actor {actor!r} is not the formation authority {authorized_actor!r}"
            )

        required_identity_fields = ("id", "name", "outcome", "owner", "domain")
        if any(not assigned.get(field) for field in required_identity_fields):
            raise FormationError("Promotion does not define a complete capability identity")
        if assigned.get("lifecycle") != LifecycleStatus.APPROVED:
            raise FormationError("A formed capability must begin in approved, inactive state")
        if assigned.get("active_ckc"):
            raise FormationError("Promotion must not activate the initial CKC implicitly")
        if snapshot.capability(str(assigned["id"])) is not None:
            raise FormationError(f"Capability identity already exists: {assigned['id']}")
        if proposal.candidate_owner != assigned.get("owner"):
            raise FormationError("Assigned owner differs from the reviewed candidate owner")

        if initial_ckc.version != 1 or initial_ckc.predecessor:
            raise FormationError("The initial CKC must be version 1 without a predecessor")
        if initial_ckc.status != "canonical-approved":
            raise FormationError("The initial CKC must be complete and canonical-approved")
        if initial_ckc.capability_ref != assigned.get("id"):
            raise FormationError("Initial CKC and assigned capability identity do not match")
        if not all(
            (
                initial_ckc.knowledge_scope,
                initial_ckc.obligations,
                initial_ckc.authorities,
                initial_ckc.evidence_contract,
                initial_ckc.evaluation_contract,
                initial_ckc.governance,
                initial_ckc.projection_rules,
                initial_ckc.source_bindings,
            )
        ):
            raise FormationError("The initial CKC is not a complete canonical contract")

        initial_refs = _ckc_refs(initial_ckc)
        append_id = append.get("id")
        formed_snapshot_ref = formation.get("formed_registry_snapshot_ref")
        expected_history = set(proposal.pattern_signal_refs)
        declared_history = set(decision.inputs.get("supporting_history_refs", []))
        provenance = initial_ckc.generated_from
        if (
            not append_id
            or not formed_snapshot_ref
            or append.get("proposal_ref") != proposal.id
            or append.get("capability_ref") != assigned.get("id")
            or append.get("initial_ckc_ref") not in initial_refs
            or append.get("authorization_decision_ref") != decision.id
            or append.get("status") != "inactive-initial-ckc"
        ):
            raise FormationError("Formation append does not match the authorized transition")
        if decision.inputs.get("proposal_ref") != proposal.id:
            raise FormationError("Decision inputs do not identify the promoted proposal")
        if decision.inputs.get("registry_snapshot_ref") != snapshot.id:
            raise FormationError("Decision does not reference the exact input Registry snapshot")
        if not expected_history.issubset(declared_history):
            raise FormationError("Decision omits recurrent history supporting the proposal")
        if (
            provenance.get("capability_proposal") != proposal.id
            or provenance.get("governance_decision") != decision.id
            or provenance.get("formation_append") != append_id
            or not expected_history.issubset(set(provenance.get("recurrent_history", [])))
        ):
            raise FormationError("Initial CKC does not preserve its formation provenance")
        if (
            initial_ckc.governance.get("immutable") is not True
            or initial_ckc.governance.get("proposal_ref") != proposal.id
            or initial_ckc.governance.get("formation_decision_ref") != decision.id
            or initial_ckc.governance.get("formation_append_ref") != append_id
        ):
            raise FormationError("Initial CKC governance does not preserve formation authority")
        if not self.repository.can_append_formation(initial_ckc, str(append_id)):
            raise FormationError("Capability formation would duplicate an existing CKC or receipt")

        capability = Capability.model_validate(assigned)
        receipt = FormationAppendReceipt(
            id=str(append_id),
            proposal_ref=proposal.id,
            decision_ref=decision.id,
            capability_ref=capability.id,
            initial_ckc_ref=f"{initial_ckc.id}@{initial_ckc.version}",
            appended_by=actor,
            appended_at=utc_now(),
        )

        # All deterministic preconditions have passed before either append-only write.
        self.repository.append_initial(initial_ckc)
        self.repository.record_formation_receipt(receipt)

        formed = snapshot.model_copy(deep=True)
        formed.id = str(formed_snapshot_ref)
        formed.generated_from = {
            "previous_registry_snapshot": snapshot.id,
            "capability_proposal": proposal.id,
            "governance_decision": decision.id,
            "formation_append": receipt.id,
        }
        formed.capabilities.append(capability)
        formed.registry["capability_count"] = len(formed.capabilities)
        formed.registry["last_transition"] = receipt.id
        return formed, receipt

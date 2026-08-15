"""
Institutional Capability Lineage Architecture (ICLA)
Reference Implementation

Copyright (c) 2026 Mariano Garralda-Barrio

Licensed under the MIT License.
See the LICENSE file in the repository root for details.
"""

# Module purpose: Governed identity, metadata, relation, and initial-CKC formation.

from typing import Any

from ..exceptions import FormationError
from ..models.capability import Capability
from ..models.ckc import CapabilityKnowledgeContract
from ..models.common import LifecycleStatus, utc_now
from ..models.governance import FormationAppendReceipt, GovernanceDecision
from ..models.proposal import CapabilityProposal, ProposalStatus
from ..models.registry import RegistryRelation, RegistrySnapshot
from ..repositories.ckc_repository import CKCRepository


def _ckc_refs(ckc: CapabilityKnowledgeContract) -> set[str]:
    return {f"{ckc.id}@{ckc.version}", f"{ckc.id}-v{ckc.version}"}


def _affirmed(value: Any) -> bool:
    return value is True or str(value).casefold() in {"approved", "pass", "passed", "confirmed"}


def _relation_key(relation: RegistryRelation) -> tuple[str, str, str]:
    return (relation.relation_type, relation.source, relation.target)


def _proposed_relation_keys(
    proposal: CapabilityProposal,
    *,
    new_capability_id: str,
    snapshot: RegistrySnapshot,
) -> set[tuple[str, str, str]]:
    keys: set[tuple[str, str, str]] = set()
    for item in proposal.proposed_relations:
        relation_type = item.get("type")
        direction = item.get("direction")
        other = item.get("other_capability_ref")
        if not relation_type or direction not in {"outgoing", "incoming"} or not other:
            raise FormationError("Proposal contains an invalid proposed capability relation")
        if snapshot.capability(str(other)) is None:
            raise FormationError(
                f"Proposed capability relation references unknown capability {other!r}"
            )
        raw = (
            {"type": relation_type, "from": new_capability_id, "to": other}
            if direction == "outgoing"
            else {"type": relation_type, "from": other, "to": new_capability_id}
        )
        try:
            relation = RegistryRelation.model_validate(raw)
        except Exception as exc:  # Pydantic preserves exact validation details upstream.
            raise FormationError(
                "Proposal contains an invalid proposed capability relation"
            ) from exc
        keys.add(_relation_key(relation))
    return keys


class CapabilityFormationService:
    """Execute governed promotion, Registry formation, and initial-CKC append."""

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
        if proposal.recurrence_assessment.get("justified_expectation") is not True:
            raise FormationError(
                "Promotion requires justified expected recurrence or continuing institutional need"
            )
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

        proposed_relation_keys = _proposed_relation_keys(
            proposal,
            new_capability_id=str(assigned["id"]),
            snapshot=snapshot,
        )
        raw_approved_relations = promotion.get("approved_relations")
        if not isinstance(raw_approved_relations, list):
            raise FormationError("Promotion must record approved capability relations")
        approved_relations: list[RegistryRelation] = []
        approved_relation_keys: set[tuple[str, str, str]] = set()
        for raw_relation in raw_approved_relations:
            try:
                relation = RegistryRelation.model_validate(raw_relation)
            except Exception as exc:
                raise FormationError("Approved capability relation is invalid") from exc
            if relation.source == relation.target:
                raise FormationError("Approved capability relation cannot be self-referential")
            if str(assigned["id"]) not in {relation.source, relation.target}:
                raise FormationError(
                    "Approved capability relation must involve the formed capability"
                )
            other = (
                relation.target
                if relation.source == str(assigned["id"])
                else relation.source
            )
            if snapshot.capability(other) is None:
                raise FormationError(
                    f"Approved capability relation references unknown capability endpoint {other!r}"
                )
            key = _relation_key(relation)
            if key not in proposed_relation_keys:
                raise FormationError("Approved capability relation was not proposed for review")
            if key in approved_relation_keys:
                raise FormationError("Approved capability relations must be unique")
            approved_relation_keys.add(key)
            approved_relations.append(relation)

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
        expected_support = set(proposal.supporting_record_refs)
        declared_support = set(decision.inputs.get("supporting_record_refs", []))
        support_entries = proposal.generated_from.get("supporting_records", [])
        required_support_fields = {
            "record_ref",
            "record_type",
            "repository_ref",
            "record_locator",
            "record_version",
            "provenance_refs",
        }
        indexed_support = {
            item.get("record_ref"): item for item in support_entries if isinstance(item, dict)
        }
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
        if expected_support - indexed_support.keys() or any(
            required_support_fields - item.keys()
            or not item.get("provenance_refs")
            for item in indexed_support.values()
        ):
            raise FormationError("Proposal has unresolved supporting-record provenance")
        if not expected_support.issubset(declared_support):
            raise FormationError("Decision omits records supporting the proposal")
        if (
            provenance.get("capability_proposal") != proposal.id
            or provenance.get("governance_decision") != decision.id
            or provenance.get("formation_append") != append_id
            or not expected_support.issubset(
                set(provenance.get("supporting_record_refs", []))
            )
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
        formed.relations.extend(approved_relations)
        formed.registry["capability_count"] = len(formed.capabilities)
        formed.registry["last_transition"] = receipt.id
        return formed, receipt

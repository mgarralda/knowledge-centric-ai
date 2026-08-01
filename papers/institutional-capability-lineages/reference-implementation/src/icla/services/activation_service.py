"""
Institutional Capability Lineages (ICLA)
Reference Implementation

Copyright (c) 2026 Mariano Garralda-Barrio

Licensed under the MIT License.
See the LICENSE file in the repository root for details.
"""

# Module purpose: Atomic active-pointer transition after, and separate from, approval.

from ..exceptions import ActivationError
from ..models.common import utc_now
from ..models.governance import ActivationRecord, GovernanceDecision


class ActivationService:
    def activate(self, snapshot, successor, decision: GovernanceDecision, *, actor: str):
        if decision.status != "approved":
            raise ActivationError("Only an approved decision can authorize activation")
        activation = decision.activation
        if (
            activation.get("capability") != successor.capability_ref
            or activation.get("ckc") != successor.id
            or activation.get("version") != successor.version
        ):
            raise ActivationError("Decision activation target does not match the successor CKC")
        updated = snapshot.model_copy(deep=True)
        capability = updated.capability(successor.capability_ref)
        if capability is None:
            raise ActivationError(f"Unknown capability {successor.capability_ref}")
        if capability.active_ckc is None:
            raise ActivationError("Only an active capability with an active CKC can be advanced")
        previous = capability.active_ckc.model_dump()
        authorized_actor = successor.governance.get("activation_authority") or capability.owner
        if actor != authorized_actor:
            raise ActivationError(
                f"Actor {actor!r} is not the declared activation authority {authorized_actor!r}"
            )
        if successor.version <= capability.active_ckc.version:
            raise ActivationError("Successor version must be newer than the active CKC")
        transition = activation.get("active_pointer_transition", {})
        expected_from = {
            f"{capability.active_ckc.id}@{capability.active_ckc.version}",
            f"{capability.active_ckc.id}-v{capability.active_ckc.version}",
        }
        expected_to = {
            f"{successor.id}@{successor.version}",
            f"{successor.id}-v{successor.version}",
        }
        authorizing_decision = successor.generated_from.get(
            "governance_decision"
        ) or successor.governance.get("admission_decision_ref")
        if authorizing_decision != decision.id:
            raise ActivationError("Successor CKC is not linked to the authorizing decision")
        predecessor_refs = {
            successor.predecessor,
            successor.generated_from.get("predecessor"),
        }
        if not expected_from & predecessor_refs:
            raise ActivationError("Successor CKC does not identify the active predecessor")
        if (
            not isinstance(transition, dict)
            or transition.get("from") not in expected_from
            or transition.get("to") not in expected_to
        ):
            raise ActivationError("Decision does not declare the exact active-pointer transition")
        if activation.get("rollback_target") not in expected_from:
            raise ActivationError("Decision does not declare the exact rollback target")
        if "future" not in str(activation.get("applies_to", "")):
            raise ActivationError("Successor activation must apply only to future resolutions")
        capability.active_ckc.id, capability.active_ckc.version = successor.id, successor.version
        record = ActivationRecord(
            id=str(activation["id"]),
            decision_ref=decision.id,
            capability_ref=capability.id,
            previous_ckc=previous,
            active_ckc=capability.active_ckc.model_dump(),
            rollback_target=previous,
            activated_by=actor,
            activated_at=utc_now(),
        )
        return updated, record

    def rollback(self, snapshot, target, decision: GovernanceDecision, *, actor: str):
        """Apply the rollback target pre-authorized by an approved activation decision."""
        if decision.status != "approved":
            raise ActivationError("Rollback requires an approved governance decision")
        activation = decision.activation
        capability = snapshot.capability(target.capability_ref)
        if capability is None or capability.active_ckc is None:
            raise ActivationError(f"Unknown or inactive capability {target.capability_ref}")
        authorized_actor = target.governance.get("activation_authority") or capability.owner
        if actor != authorized_actor:
            raise ActivationError(
                f"Actor {actor!r} is not the declared activation authority {authorized_actor!r}"
            )
        transition = activation.get("active_pointer_transition", {})
        target_refs = {f"{target.id}@{target.version}", f"{target.id}-v{target.version}"}
        current_refs = {
            f"{capability.active_ckc.id}@{capability.active_ckc.version}",
            f"{capability.active_ckc.id}-v{capability.active_ckc.version}",
        }
        if activation.get("rollback_target") not in target_refs:
            raise ActivationError("Requested CKC is not the approved rollback target")
        if not isinstance(transition, dict) or transition.get("to") not in current_refs:
            raise ActivationError("Current active CKC is not the state authorized for rollback")

        updated = snapshot.model_copy(deep=True)
        updated_capability = updated.capability(target.capability_ref)
        assert updated_capability is not None and updated_capability.active_ckc is not None
        previous = updated_capability.active_ckc.model_dump()
        updated_capability.active_ckc.id = target.id
        updated_capability.active_ckc.version = target.version
        record = ActivationRecord(
            id=f"RBK-{activation['id']}",
            decision_ref=decision.id,
            capability_ref=updated_capability.id,
            previous_ckc=previous,
            active_ckc=updated_capability.active_ckc.model_dump(),
            rollback_target=updated_capability.active_ckc.model_dump(),
            action="rollback",
            activated_by=actor,
            activated_at=utc_now(),
        )
        return updated, record

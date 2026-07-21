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
        if (
            not isinstance(transition, dict)
            or transition.get("from") not in expected_from
            or transition.get("to") not in expected_to
        ):
            raise ActivationError("Decision does not declare the exact active-pointer transition")
        if "future" not in str(activation.get("applies_to", "")):
            raise ActivationError("Successor activation must apply only to future resolutions")
        capability.active_ckc.id, capability.active_ckc.version = successor.id, successor.version
        record = ActivationRecord(
            id=str(activation["id"]),
            decision_ref=decision.id,
            capability_ref=capability.id,
            previous_ckc=previous,
            active_ckc=capability.active_ckc.model_dump(),
            activated_by=actor,
            activated_at=utc_now(),
        )
        return updated, record

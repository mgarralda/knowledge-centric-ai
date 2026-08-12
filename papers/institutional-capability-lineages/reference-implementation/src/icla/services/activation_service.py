"""
Institutional Capability Lineage Architecture (ICLA)
Reference Implementation

Copyright (c) 2026 Mariano Garralda-Barrio

Licensed under the MIT License.
See the LICENSE file in the repository root for details.
"""

# Module purpose: Atomic pointer transition for an appended lineage CKC.

from ..exceptions import ActivationError, ArtifactNotFoundError
from ..models.capability import ActiveCKC
from ..models.common import LifecycleStatus, utc_now
from ..models.governance import ActivationRecord, GovernanceDecision
from ..repositories.ckc_repository import CKCRepository


class ActivationService:
    def __init__(self, repository: CKCRepository) -> None:
        self.repository = repository

    def activate(self, snapshot, appended_lineage_ckc, decision: GovernanceDecision, *, actor: str):
        """Activate an appended successor or initial CKC in a new Registry snapshot."""
        if decision.status != "approved":
            raise ActivationError("Only an approved decision can authorize activation")
        try:
            stored_ckc = self.repository.get_version(
                appended_lineage_ckc.id,
                appended_lineage_ckc.version,
            )
        except ArtifactNotFoundError as error:
            raise ActivationError(
                "Only a previously appended lineage CKC can be activated"
            ) from error
        if stored_ckc != appended_lineage_ckc:
            raise ActivationError("Appended lineage CKC differs from the activation target")
        activation = decision.activation
        if (
            activation.get("capability") != appended_lineage_ckc.capability_ref
            or activation.get("ckc") != appended_lineage_ckc.id
            or activation.get("version") != appended_lineage_ckc.version
        ):
            raise ActivationError("Decision activation target does not match the appended CKC")
        updated = snapshot.model_copy(deep=True)
        capability = updated.capability(appended_lineage_ckc.capability_ref)
        if capability is None:
            raise ActivationError(f"Unknown capability {appended_lineage_ckc.capability_ref}")
        if capability.active_ckc is None:
            return self._activate_initial(
                updated,
                capability,
                appended_lineage_ckc,
                decision,
                actor=actor,
            )
        try:
            append_receipt = self.repository.get_append_receipt(
                appended_lineage_ckc.id,
                appended_lineage_ckc.version,
            )
        except ArtifactNotFoundError as error:
            raise ActivationError("Successor CKC has no append receipt") from error
        if (
            append_receipt.capability_ref != capability.id
            or append_receipt.status != "inactive-successor"
            or activation.get("successor_append_ref") != append_receipt.id
        ):
            raise ActivationError("Activation does not reference the exact successor append")
        previous = capability.active_ckc.model_dump()
        authorized_actor = (
            appended_lineage_ckc.governance.get("activation_authority") or capability.owner
        )
        if actor != authorized_actor:
            raise ActivationError(
                f"Actor {actor!r} is not the declared activation authority {authorized_actor!r}"
            )
        if appended_lineage_ckc.version <= capability.active_ckc.version:
            raise ActivationError("Appended CKC version must be newer than the active CKC")
        transition = activation.get("active_pointer_transition", {})
        expected_from = {
            f"{capability.active_ckc.id}@{capability.active_ckc.version}",
            f"{capability.active_ckc.id}-v{capability.active_ckc.version}",
        }
        expected_to = {
            f"{appended_lineage_ckc.id}@{appended_lineage_ckc.version}",
            f"{appended_lineage_ckc.id}-v{appended_lineage_ckc.version}",
        }
        predecessor_refs = {
            appended_lineage_ckc.predecessor,
            appended_lineage_ckc.generated_from.get("predecessor"),
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
        capability.active_ckc.id = appended_lineage_ckc.id
        capability.active_ckc.version = appended_lineage_ckc.version
        record = ActivationRecord(
            id=str(activation["id"]),
            decision_ref=decision.id,
            capability_ref=capability.id,
            activation_kind="successor",
            successor_append_ref=append_receipt.id,
            previous_ckc=previous,
            active_ckc=capability.active_ckc.model_dump(),
            rollback_target=previous,
            activated_by=actor,
            activated_at=utc_now(),
        )
        return updated, record

    def _activate_initial(
        self,
        updated,
        capability,
        initial_ckc,
        decision: GovernanceDecision,
        *,
        actor: str,
    ):
        if capability.lifecycle != LifecycleStatus.APPROVED:
            raise ActivationError("Initial activation requires an approved, inactive capability")
        if initial_ckc.version != 1 or initial_ckc.predecessor:
            raise ActivationError("Initial activation requires an initial CKC v1")
        try:
            formation_receipt = self.repository.get_formation_receipt(
                initial_ckc.id,
                initial_ckc.version,
            )
        except ArtifactNotFoundError as error:
            raise ActivationError("Initial CKC has no governed formation append") from error

        activation = decision.activation
        transition = activation.get("active_pointer_transition", {})
        target_refs = {
            f"{initial_ckc.id}@{initial_ckc.version}",
            f"{initial_ckc.id}-v{initial_ckc.version}",
        }
        if (
            activation.get("activation_kind") != "initial"
            or activation.get("formation_append_ref") != formation_receipt.id
            or formation_receipt.capability_ref != capability.id
            or formation_receipt.status != "inactive-initial-ckc"
            or transition.get("from") is not None
            or transition.get("to") not in target_refs
            or activation.get("rollback_target") is not None
        ):
            raise ActivationError(
                "Initial activation is not separate from the exact formation append"
            )
        if "future" not in str(activation.get("applies_to", "")):
            raise ActivationError("Initial activation must apply only to future resolutions")
        authorized_actor = initial_ckc.governance.get("activation_authority") or capability.owner
        if actor != authorized_actor:
            raise ActivationError(
                f"Actor {actor!r} is not the declared activation authority {authorized_actor!r}"
            )

        capability.active_ckc = ActiveCKC(id=initial_ckc.id, version=initial_ckc.version)
        capability.lifecycle = LifecycleStatus.ACTIVE
        resulting_snapshot_ref = activation.get("resulting_registry_snapshot_ref")
        if not resulting_snapshot_ref:
            raise ActivationError("Initial activation lacks its resulting Registry snapshot")
        previous_snapshot_ref = updated.id
        updated.id = str(resulting_snapshot_ref)
        updated.generated_from = {
            "previous_registry_snapshot": previous_snapshot_ref,
            "governance_decision": decision.id,
            "formation_append": formation_receipt.id,
            "activation": activation["id"],
        }
        updated.registry["last_transition"] = activation["id"]
        record = ActivationRecord(
            id=str(activation["id"]),
            decision_ref=decision.id,
            capability_ref=capability.id,
            activation_kind="initial",
            formation_append_ref=formation_receipt.id,
            previous_ckc=None,
            active_ckc=capability.active_ckc.model_dump(),
            rollback_target=None,
            activated_by=actor,
            activated_at=utc_now(),
        )
        return updated, record

    def rollback(self, snapshot, target, decision: GovernanceDecision, *, actor: str):
        """Reactivate an eligible retained CKC through a new approved activation decision."""
        if decision.status != "approved":
            raise ActivationError("Reactivation requires an approved governance decision")
        try:
            stored_target = self.repository.get_version(target.id, target.version)
        except ArtifactNotFoundError as error:
            raise ActivationError(
                "Reactivation target is not in the governed CKC lineage"
            ) from error
        if stored_target != target:
            raise ActivationError("Stored retained target differs from the requested CKC")
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
        if (
            activation.get("activation_kind") != "reactivation"
            or activation.get("capability") != target.capability_ref
            or activation.get("ckc") != target.id
            or activation.get("version") != target.version
        ):
            raise ActivationError("Requested retained CKC is not the approved reactivation target")
        if (
            not isinstance(transition, dict)
            or transition.get("from") not in current_refs
            or transition.get("to") not in target_refs
            or activation.get("rollback_target") not in current_refs
        ):
            raise ActivationError(
                "Reactivation requires a new activation decision from the current CKC "
                "to the retained target"
            )

        updated = snapshot.model_copy(deep=True)
        updated_capability = updated.capability(target.capability_ref)
        assert updated_capability is not None and updated_capability.active_ckc is not None
        previous = updated_capability.active_ckc.model_dump()
        updated_capability.active_ckc.id = target.id
        updated_capability.active_ckc.version = target.version
        record = ActivationRecord(
            id=str(activation["id"]),
            decision_ref=decision.id,
            capability_ref=updated_capability.id,
            activation_kind="reactivation",
            previous_ckc=previous,
            active_ckc=updated_capability.active_ckc.model_dump(),
            rollback_target=previous,
            action="reactivate",
            activated_by=actor,
            activated_at=utc_now(),
        )
        return updated, record

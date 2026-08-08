from pathlib import Path

import pytest

from icla.api.facade import ICLA
from icla.config import Settings
from icla.exceptions import ActivationError, FormationError
from icla.models.capability import Capability
from icla.models.ckc import CapabilityKnowledgeContract
from icla.models.governance import GovernanceDecision
from icla.models.proposal import CapabilityProposal
from icla.models.registry import RegistrySnapshot
from icla.repositories import CKCRepository
from icla.services import ActivationService, CapabilityFormationService, LineageService
from icla.specification import ArtifactValidator, ConformanceChecker, ConformanceProfile
from icla.storage import AppendOnlyStore

TRACE = (
    Path(__file__).resolve().parents[3]
    / "specification"
    / "reference-traces"
    / "auth-evolution-formation"
)


def artifacts():
    validator = ArtifactValidator()
    return {path.stem: validator.validate_file(path) for path in sorted(TRACE.glob("*.yaml"))}


def inputs():
    values = artifacts()
    return (
        values,
        RegistrySnapshot.model_validate(values["registry-before"]),
        CapabilityProposal.model_validate(values["capability-proposal"]),
        CapabilityKnowledgeContract.model_validate(values["ckc-auth-evol-v1"]),
        GovernanceDecision.model_validate(values["governance-decision"]),
    )


@pytest.mark.skipif(not TRACE.is_dir(), reason="formation reference artifacts are not published")
def test_auth_evolution_formation_trace_conforms_to_evolving_profile():
    values = artifacts()
    ConformanceChecker().require_trace(values.values(), ConformanceProfile.EVOLVING)


@pytest.mark.skipif(not TRACE.is_dir(), reason="formation reference artifacts are not published")
def test_governed_formation_and_initial_activation_replay_the_published_states(tmp_path):
    values, before, proposal, initial_ckc, decision = inputs()
    facade = ICLA(Settings(data_dir=tmp_path))
    facade.adjudicate(
        decision,
        reviewer="institutional-capability-governance-board",
        policy_refs=["POL-CAPABILITY-FORMATION"],
    )

    formed, receipt = facade.promote_capability(
        before,
        proposal,
        initial_ckc,
        decision,
        actor="institutional-capability-governance-board",
    )

    assert formed == RegistrySnapshot.model_validate(values["registry-formed"])
    assert before.capability("CAP-AUTH-EVOL") is None
    assert formed.capability("CAP-AUTH-EVOL").active_ckc is None
    assert formed.capability("CAP-AUTH-EVOL").lifecycle == "approved"
    assert receipt.status == "inactive-initial-ckc"
    assert receipt.initial_ckc_ref == "CKC-AUTH-EVOL@1"
    assert facade.ckc_repository.get_latest_governed_version("CKC-AUTH-EVOL") == initial_ckc
    assert facade.governance_repository.get_decision(decision.id) == decision

    active, activation = facade.activate_ckc(
        formed,
        initial_ckc,
        decision,
        actor="identity-and-api-governance-review",
    )

    assert active == RegistrySnapshot.model_validate(values["registry-active"])
    assert formed.capability("CAP-AUTH-EVOL").active_ckc is None
    assert active.capability("CAP-AUTH-EVOL").active_ckc.version == 1
    assert activation.id == "ACT-AUTH-EVOL-001"
    assert activation.activation_kind == "initial"
    assert activation.formation_append_ref == receipt.id
    assert activation.previous_ckc is None
    assert activation.rollback_target is None
    assert facade.governance_repository.get_activation(activation.id) == activation


def test_candidate_proposal_cannot_be_promoted_and_leaves_no_partial_write(tmp_path):
    _, before, proposal, initial_ckc, decision = inputs()
    proposal.status = "candidate"
    repository = CKCRepository(AppendOnlyStore(tmp_path))

    with pytest.raises(FormationError, match="submitted proposal"):
        CapabilityFormationService(repository).promote(
            before,
            proposal,
            initial_ckc,
            decision,
            actor="institutional-capability-governance-board",
        )

    assert repository.store.list("ckcs") == []
    assert repository.store.list("formation-append-receipts") == []


def test_unauthorized_promotion_leaves_no_partial_write(tmp_path):
    _, before, proposal, initial_ckc, decision = inputs()
    repository = CKCRepository(AppendOnlyStore(tmp_path))

    with pytest.raises(FormationError, match="formation authority"):
        CapabilityFormationService(repository).promote(
            before,
            proposal,
            initial_ckc,
            decision,
            actor="OTHER",
        )

    assert repository.store.list("ckcs") == []
    assert repository.store.list("formation-append-receipts") == []


def test_rejected_governance_decision_cannot_form_capability(tmp_path):
    _, before, proposal, initial_ckc, decision = inputs()
    decision.status = "rejected"
    repository = CKCRepository(AppendOnlyStore(tmp_path))

    with pytest.raises(FormationError, match="approved capability-formation decision"):
        CapabilityFormationService(repository).promote(
            before,
            proposal,
            initial_ckc,
            decision,
            actor="institutional-capability-governance-board",
        )

    assert repository.store.list("ckcs") == []
    assert repository.store.list("formation-append-receipts") == []


def test_missing_formed_snapshot_reference_leaves_no_partial_write(tmp_path):
    _, before, proposal, initial_ckc, decision = inputs()
    decision.capability_formation.pop("formed_registry_snapshot_ref")
    repository = CKCRepository(AppendOnlyStore(tmp_path))

    with pytest.raises(FormationError, match="Formation append"):
        CapabilityFormationService(repository).promote(
            before,
            proposal,
            initial_ckc,
            decision,
            actor="institutional-capability-governance-board",
        )

    assert repository.store.list("ckcs") == []
    assert repository.store.list("formation-append-receipts") == []


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (lambda ckc: setattr(ckc, "version", 2), "version 1"),
        (
            lambda ckc: ckc.generated_from.update({"capability_proposal": "PROP-OTHER"}),
            "formation provenance",
        ),
        (
            lambda ckc: ckc.governance.update({"formation_append_ref": "FORM-OTHER"}),
            "formation authority",
        ),
    ],
)
def test_invalid_initial_ckc_is_rejected_before_any_write(tmp_path, mutation, message):
    _, before, proposal, initial_ckc, decision = inputs()
    mutation(initial_ckc)
    repository = CKCRepository(AppendOnlyStore(tmp_path))

    with pytest.raises(FormationError, match=message):
        CapabilityFormationService(repository).promote(
            before,
            proposal,
            initial_ckc,
            decision,
            actor="institutional-capability-governance-board",
        )

    assert repository.store.list("ckcs") == []
    assert repository.store.list("formation-append-receipts") == []


def test_duplicate_capability_identity_is_rejected_before_any_write(tmp_path):
    _, before, proposal, initial_ckc, decision = inputs()
    before.capabilities.append(
        Capability.model_validate(
            decision.capability_formation["governed_promotion"]["assigned_capability"]
        )
    )
    repository = CKCRepository(AppendOnlyStore(tmp_path))

    with pytest.raises(FormationError, match="already exists"):
        CapabilityFormationService(repository).promote(
            before,
            proposal,
            initial_ckc,
            decision,
            actor="institutional-capability-governance-board",
        )

    assert repository.store.list("ckcs") == []


def test_initial_activation_requires_the_exact_formation_append(tmp_path):
    _, before, proposal, initial_ckc, decision = inputs()
    repository = CKCRepository(AppendOnlyStore(tmp_path))
    formed, _ = CapabilityFormationService(repository).promote(
        before,
        proposal,
        initial_ckc,
        decision,
        actor="institutional-capability-governance-board",
    )
    invalid = decision.model_copy(deep=True)
    invalid.activation["formation_append_ref"] = "FORM-OTHER"

    with pytest.raises(ActivationError, match="exact formation append"):
        ActivationService(repository).activate(
            formed,
            initial_ckc,
            invalid,
            actor="identity-and-api-governance-review",
        )

    assert formed.capability("CAP-AUTH-EVOL").active_ckc is None


def test_initial_activation_cannot_run_before_formation(tmp_path):
    _, _, _, initial_ckc, decision = inputs()
    formed = RegistrySnapshot.model_validate(artifacts()["registry-formed"])

    with pytest.raises(ActivationError, match="previously appended"):
        ActivationService(CKCRepository(AppendOnlyStore(tmp_path))).activate(
            formed,
            initial_ckc,
            decision,
            actor="identity-and-api-governance-review",
        )


def test_second_promotion_is_rejected_without_changing_retained_state(tmp_path):
    _, before, proposal, initial_ckc, decision = inputs()
    repository = CKCRepository(AppendOnlyStore(tmp_path))
    service = CapabilityFormationService(repository)
    service.promote(
        before,
        proposal,
        initial_ckc,
        decision,
        actor="institutional-capability-governance-board",
    )

    with pytest.raises(FormationError, match="duplicate"):
        service.promote(
            before,
            proposal,
            initial_ckc,
            decision,
            actor="institutional-capability-governance-board",
        )

    assert len(repository.store.list("ckcs")) == 1
    assert len(repository.store.list("formation-append-receipts")) == 1


def test_formation_lineage_connects_history_proposal_decision_identity_ckc_and_activation():
    values = artifacts()
    lineage = LineageService().build_lineage("CAP-AUTH-EVOL", list(values.values()))
    LineageService.validate_connected_lineage(lineage)
    reachable = LineageService()._reachable("PROP-AUTH-EVOL-01", lineage)

    assert {
        "ASM-OAUTH-042",
        "EVD-AUTH-ROTATION-017",
        "DEC-AUTH-EVOL-FORMATION-001",
        "FORM-AUTH-EVOL-001",
        "CAP-AUTH-EVOL",
        "CKC-AUTH-EVOL@1",
        "ACT-AUTH-EVOL-001",
    } <= reachable


def test_trace_rejects_implicit_activation_and_missing_formation_provenance():
    values = artifacts()
    values["registry-formed"]["capabilities"][-1]["lifecycle"] = "active"
    values["registry-formed"]["capabilities"][-1]["active_ckc"] = {
        "id": "CKC-AUTH-EVOL",
        "version": 1,
    }
    values["ckc-auth-evol-v1"]["generated_from"]["capability_proposal"] = "PROP-OTHER"

    errors = ConformanceChecker().check_trace(values.values(), ConformanceProfile.EVOLVING)

    assert "ICLA-11: promotion does not preserve a formed, inactive state" in errors
    assert "ICLA-11: initial CKC loses its proposal, decision, or history origin" in errors

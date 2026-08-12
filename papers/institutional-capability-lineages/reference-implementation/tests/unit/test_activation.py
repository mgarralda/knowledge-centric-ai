import pytest

from icla.api.facade import ICLA
from icla.config import Settings
from icla.exceptions import ActivationError, SuccessionError
from icla.models.capability import ActiveCKC, Capability
from icla.models.ckc import CapabilityKnowledgeContract
from icla.models.governance import GovernanceDecision
from icla.models.registry import RegistrySnapshot
from icla.repositories.ckc_repository import CKCRepository
from icla.services.activation_service import ActivationService
from icla.services.succession_service import SuccessionService
from icla.storage import AppendOnlyStore


def snapshot():
    return RegistrySnapshot(
        id="REG-SNAP-1",
        generated_from={"source": "test"},
        registry={
            "logical_registry_id": "REG",
            "snapshot_status": "immutable",
            "capability_count": 1,
            "active_pointer_policy": "governed",
        },
        capabilities=[
            Capability(
                id="CAP-VERIFY",
                name="Verify",
                outcome="verify",
                owner="OWNER",
                domain="security",
                lifecycle="active",
                active_ckc=ActiveCKC(id="CKC-VERIFY", version=9),
            )
        ],
    )


def snapshot_with_unrelated_capability():
    value = snapshot()
    value.capabilities.append(
        Capability(
            id="CAP-OTHER",
            name="Other",
            outcome="other",
            owner="OTHER-OWNER",
            domain="operations",
            lifecycle="active",
            active_ckc=ActiveCKC(id="CKC-OTHER", version=3),
        )
    )
    value.registry["capability_count"] = 2
    return value


def successor():
    return CapabilityKnowledgeContract(
        id="CKC-VERIFY",
        generated_from={
            "predecessor": "CKC-VERIFY@9",
            "governance_decision": "DEC-1",
            "successor_delta": "DELTA-VERIFY-009-010",
        },
        capability_ref="CAP-VERIFY",
        version=10,
        status="canonical-approved",
        predecessor="CKC-VERIFY@9",
        knowledge_scope={},
        obligations=[],
        evidence_contract={},
        evaluation_contract={},
        governance={
            "admission_decision_ref": "DEC-1",
            "successor_delta_ref": "DELTA-VERIFY-009-010",
        },
        projection_rules={},
        source_bindings=[],
    )


def predecessor():
    return CapabilityKnowledgeContract(
        id="CKC-VERIFY",
        generated_from={"source": "retained-lineage"},
        capability_ref="CAP-VERIFY",
        version=9,
        status="superseded",
        predecessor="CKC-VERIFY@8",
        knowledge_scope={},
        obligations=[],
        evidence_contract={},
        evaluation_contract={},
        governance={},
        projection_rules={},
        source_bindings=[],
    )


def decision(status="approved"):
    return GovernanceDecision(
        id="DEC-1",
        schema_ref="schemas/governance-decision.schema.yaml",
        generated_from={"evidence": "E", "review": "R", "policy": "P"},
        status=status,
        inputs={},
        review={},
        dispositions={},
        impact_record={
            "id": "IMP-1",
            "affected_capabilities": ["CAP-VERIFY"],
            "affected_ckcs": ["CKC-VERIFY@9", "CKC-VERIFY@10"],
            "review_required": True,
        },
        successor_delta={
            "id": "DELTA-VERIFY-009-010",
            "predecessor_ref": "CKC-VERIFY@9",
            "successor_ref": "CKC-VERIFY@10",
            "changed_commitments": [
                {
                    "area": "evaluation_contract",
                    "operation": "add",
                    "subject": "governed compatibility validation",
                }
            ],
            "rationale": "Qualified evidence supports reuse",
            "supporting_evidence_refs": ["EVD-1"],
            "authorization_decision_ref": "DEC-1",
            "rollback_ref": "CKC-VERIFY@9",
            "successor_complete": True,
            "reconstruction_patch": False,
        },
        successor_append={
            "id": "APPEND-VERIFY-010",
            "capability": "CAP-VERIFY",
            "predecessor_ref": "CKC-VERIFY@9",
            "successor_ref": "CKC-VERIFY@10",
            "delta_ref": "DELTA-VERIFY-009-010",
            "authorization_decision_ref": "DEC-1",
            "status": "inactive-successor",
        },
        activation={
            "id": "ACT-1",
            "capability": "CAP-VERIFY",
            "ckc": "CKC-VERIFY",
            "version": 10,
            "successor_append_ref": "APPEND-VERIFY-010",
            "applies_to": "future-resolutions-only",
            "active_pointer_transition": {
                "from": "CKC-VERIFY@9",
                "to": "CKC-VERIFY@10",
            },
            "rollback_target": "CKC-VERIFY@9",
        },
        historical_immutability={},
        capability_formation={},
        resulting_lineage_edges=[{"type": "activated_by", "from": "CKC-VERIFY@10", "to": "DEC-1"}],
    )


def reactivation_decision(status="approved"):
    value = decision(status).model_copy(deep=True)
    value.id = "DEC-REACTIVATE-1"
    value.activation = {
        "id": "ACT-REACTIVATE-1",
        "activation_kind": "reactivation",
        "capability": "CAP-VERIFY",
        "ckc": "CKC-VERIFY",
        "version": 9,
        "applies_to": "future-resolutions-only",
        "active_pointer_transition": {
            "from": "CKC-VERIFY@10",
            "to": "CKC-VERIFY@9",
        },
        "rollback_target": "CKC-VERIFY@10",
    }
    value.resulting_lineage_edges = [
        {"type": "reactivates", "from": "ACT-REACTIVATE-1", "to": "CKC-VERIFY@9"}
    ]
    return value


def governed_services(tmp_path):
    repository = CKCRepository(AppendOnlyStore(tmp_path))
    repository.append_successor(predecessor())
    return repository, SuccessionService(repository), ActivationService(repository)


def append_governed_successor(tmp_path, declared=None):
    declared = declared or decision()
    repository, succession, activation = governed_services(tmp_path)
    receipt = succession.append_successor(
        snapshot().capability("CAP-VERIFY"),
        predecessor(),
        successor(),
        declared,
        actor="OWNER",
    )
    return repository, activation, receipt


def test_append_and_activation_are_distinct_and_historical_snapshot_is_unchanged(tmp_path):
    old = snapshot()
    repository, activation_service, receipt = append_governed_successor(tmp_path)

    assert old.capability("CAP-VERIFY").active_ckc.version == 9
    assert repository.get_latest_governed_version("CKC-VERIFY").version == 10
    assert receipt.status == "inactive-successor"

    updated, record = activation_service.activate(old, successor(), decision(), actor="OWNER")
    assert old.capability("CAP-VERIFY").active_ckc.version == 9
    assert updated.capability("CAP-VERIFY").active_ckc.version == 10
    assert record.id == "ACT-1"
    assert record.previous_ckc["version"] == 9
    assert record.rollback_target["version"] == 9
    assert record.successor_append_ref == receipt.id


def test_activation_changes_only_the_target_pointer_mapping(tmp_path):
    _, service, _ = append_governed_successor(tmp_path)
    original = snapshot_with_unrelated_capability()

    updated, _ = service.activate(original, successor(), decision(), actor="OWNER")

    assert original.capability("CAP-VERIFY").active_ckc.version == 9
    assert updated.capability("CAP-VERIFY").active_ckc.version == 10
    assert updated.capability("CAP-OTHER") == original.capability("CAP-OTHER")
    assert len(updated.capabilities) == len(original.capabilities)


def test_approved_rollback_restores_the_exact_predecessor_without_mutating_history(tmp_path):
    _, service, _ = append_governed_successor(tmp_path)
    original = snapshot()
    advanced, activation = service.activate(
        original,
        successor(),
        decision(),
        actor="OWNER",
    )

    restored, rollback = service.rollback(
        advanced,
        predecessor(),
        reactivation_decision(),
        actor="OWNER",
    )

    assert original.capability("CAP-VERIFY").active_ckc.version == 9
    assert advanced.capability("CAP-VERIFY").active_ckc.version == 10
    assert restored.capability("CAP-VERIFY").active_ckc.version == 9
    assert activation.action == "activate"
    assert rollback.action == "reactivate"
    assert rollback.id == "ACT-REACTIVATE-1"
    assert rollback.decision_ref == "DEC-REACTIVATE-1"
    assert rollback.activation_kind == "reactivation"
    assert rollback.previous_ckc["version"] == 10


def test_reactivation_cannot_reuse_the_forward_activation_decision(tmp_path):
    _, service, _ = append_governed_successor(tmp_path)
    advanced, _ = service.activate(snapshot(), successor(), decision(), actor="OWNER")

    with pytest.raises(ActivationError, match="approved reactivation target"):
        service.rollback(advanced, predecessor(), decision(), actor="OWNER")


def test_rejected_decision_cannot_activate(tmp_path):
    _, service, _ = append_governed_successor(tmp_path)
    with pytest.raises(ActivationError):
        service.activate(snapshot(), successor(), decision("rejected"), actor="OWNER")


def test_unappended_successor_cannot_activate(tmp_path):
    repository, _, service = governed_services(tmp_path)
    assert repository.get_latest_governed_version("CKC-VERIFY").version == 9
    with pytest.raises(ActivationError, match="previously appended"):
        service.activate(snapshot(), successor(), decision(), actor="OWNER")


def test_append_rejects_a_delta_that_does_not_describe_the_complete_successor(tmp_path):
    _, succession, _ = governed_services(tmp_path)
    incomplete = decision().model_copy(deep=True)
    incomplete.successor_delta["successor_complete"] = False

    with pytest.raises(SuccessionError, match="complete successor"):
        succession.append_successor(
            snapshot().capability("CAP-VERIFY"),
            predecessor(),
            successor(),
            incomplete,
            actor="OWNER",
        )


def test_icla_9_rejects_stale_predecessor_without_creating_a_branch(tmp_path):
    repository, succession, _ = governed_services(tmp_path)
    succession.append_successor(
        snapshot().capability("CAP-VERIFY"),
        predecessor(),
        successor(),
        decision(),
        actor="OWNER",
    )

    with pytest.raises(SuccessionError, match="stale-predecessor"):
        succession.append_successor(
            snapshot().capability("CAP-VERIFY"),
            predecessor(),
            successor(),
            decision(),
            actor="OWNER",
        )

    assert [item.version for item in repository.list_lineage("CKC-VERIFY")] == [9, 10]


def test_activation_rejects_an_undeclared_authority(tmp_path):
    _, service, _ = append_governed_successor(tmp_path)
    with pytest.raises(ActivationError, match="activation authority"):
        service.activate(snapshot(), successor(), decision(), actor="OTHER")


def test_activation_decision_may_be_separate_from_construction_decision(tmp_path):
    _, service, receipt = append_governed_successor(tmp_path)
    activation_decision = decision().model_copy(deep=True)
    activation_decision.id = "DEC-ACT-1"
    activation_decision.successor_delta = {}
    activation_decision.successor_append = {}
    activation_decision.activation["successor_append_ref"] = receipt.id

    updated, record = service.activate(snapshot(), successor(), activation_decision, actor="OWNER")

    assert updated.capability("CAP-VERIFY").active_ckc.version == 10
    assert record.decision_ref == "DEC-ACT-1"


def test_facade_owns_and_persists_governance_service(tmp_path):
    facade = ICLA(Settings(data_dir=tmp_path))
    declared = decision()

    result = facade.adjudicate(
        declared,
        reviewer="OWNER",
        policy_refs=["POL-GOVERNANCE"],
    )

    assert result == declared
    assert facade.governance_repository.get_decision(declared.id) == declared


def test_facade_distinguishes_active_from_latest_governed_ckc(tmp_path):
    facade = ICLA(Settings(data_dir=tmp_path))
    facade.ckc_repository.append_successor(predecessor())
    receipt = facade.append_successor(
        snapshot().capability("CAP-VERIFY"),
        predecessor(),
        successor(),
        decision(),
        actor="OWNER",
    )

    view = facade.get_capability(snapshot(), "CAP-VERIFY")

    assert receipt.status == "inactive-successor"
    assert view["selected_ckc"].version == 9
    assert view["active_ckc"].version == 9
    assert view["latest_governed_ckc"].version == 10
    assert [item.version for item in view["ckc_lineage"]] == [9, 10]

    latest = facade.get_capability(snapshot(), "CAP-VERIFY", version_policy="latest-governed")
    exact = facade.get_capability(
        snapshot(), "CAP-VERIFY", version_policy="exact", exact_version=10
    )
    assert latest["selected_ckc"].version == 10
    assert exact["selected_ckc"].version == 10

import pytest

from icla.api.facade import ICLA
from icla.config import Settings
from icla.exceptions import ActivationError
from icla.models.capability import ActiveCKC, Capability
from icla.models.ckc import CapabilityKnowledgeContract
from icla.models.governance import GovernanceDecision
from icla.models.registry import RegistrySnapshot
from icla.services.activation_service import ActivationService


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


def successor():
    return CapabilityKnowledgeContract(
        id="CKC-VERIFY",
        generated_from={"predecessor": "v9"},
        capability_ref="CAP-VERIFY",
        version=10,
        status="canonical-approved",
        predecessor="CKC-VERIFY@9",
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
        activation={
            "id": "ACT-1",
            "capability": "CAP-VERIFY",
            "ckc": "CKC-VERIFY",
            "version": 10,
            "applies_to": "future-resolutions-only",
            "active_pointer_transition": {
                "from": "CKC-VERIFY@9",
                "to": "CKC-VERIFY@10",
            },
        },
        historical_immutability={},
        capability_formation={},
        resulting_lineage_edges=[{"type": "activated_by", "from": "CKC-VERIFY@10", "to": "DEC-1"}],
    )


def test_approval_and_activation_are_separate_and_historical_snapshot_is_unchanged():
    old = snapshot()
    updated, record = ActivationService().activate(old, successor(), decision(), actor="OWNER")
    assert old.capability("CAP-VERIFY").active_ckc.version == 9
    assert updated.capability("CAP-VERIFY").active_ckc.version == 10
    assert record.id == "ACT-1"
    assert record.previous_ckc["version"] == 9


def test_rejected_decision_cannot_activate():
    with pytest.raises(ActivationError):
        ActivationService().activate(snapshot(), successor(), decision("rejected"), actor="OWNER")


def test_activation_rejects_an_undeclared_authority():
    with pytest.raises(ActivationError, match="activation authority"):
        ActivationService().activate(snapshot(), successor(), decision(), actor="OTHER")


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

import pytest

from icla.models.assembly import Assembly
from icla.policies import assess_reresolution
from icla.services.materialization_service import AccessHandleMaterializer


def assembly() -> Assembly:
    return Assembly(
        id="ASM-TEST",
        generated_from={"intent": "INT-1", "resolution": "RES-1"},
        lineage={"cee_ref": "CEE-1"},
        ckc_snapshot=[{"capability": "CAP-1", "ckc": "CKC-1", "version": 1}],
        transformation_snapshot=[{"id": "TRANSFORM-1", "version": 2}],
        operational_mandate={
            "authority_scope": "execution-scoped",
            "institutional_change_authority": False,
            "local_autonomy": ["reasoning", "iteration"],
            "evidence_disclosure": "evidence-contract-only",
            "registry_interaction": "reresolution-or-evidence-only",
            "reresolution_triggers": ["intent-materially-changed"],
        },
        selection={"included": ["CAP-1"], "excluded": []},
        evaluation_contract={"id": "EVAL-1", "version": 3, "metrics": []},
        evidence_contract={
            "id": "EVIDENCE-1",
            "version": 4,
            "selection_mode": "contract-selected",
        },
        correctness={"mandate_bounded": True},
        access_policy_ref="POL-ACCESS-1",
    )


def test_access_handle_materialization_preserves_sources_without_copying_payloads():
    handles = [
        {
            "id": "HANDLE-POLICY-1",
            "uri": "https://knowledge.example/policies/identity/8",
            "authority": "security-governance",
            "version": 8,
        }
    ]

    materialization = AccessHandleMaterializer().materialize(assembly(), handles)

    assert materialization.assembly_ref == "ASM-TEST"
    assert materialization.cee_ref == "CEE-1"
    assert materialization.substrate.model_dump() == {
        "id": "governed-access-handles",
        "version": 1,
    }
    assert materialization.transformation.model_dump() == {"id": "TRANSFORM-1", "version": 2}
    assert materialization.representation.kind == "access-handles"
    assert materialization.representation.control == "cee-controlled"
    assert materialization.representation.payload_retention == "policy-dependent"
    assert materialization.access.policy_ref == "POL-ACCESS-1"
    assert materialization.access.handles == handles
    assert materialization.evaluation_binding.model_dump() == {"id": "EVAL-1", "version": 3}
    assert materialization.evidence_binding.model_dump() == {"id": "EVIDENCE-1", "version": 4}
    assert materialization.preserves_assembly_semantics is True
    assert materialization.preserves_assembly_authority is True


def test_access_handle_materialization_requires_governed_descriptors():
    with pytest.raises(ValueError, match="id, uri, and authority"):
        AccessHandleMaterializer().materialize(assembly(), [{"id": "HANDLE-1"}])


def test_reresolution_is_event_driven_not_stepwise():
    required, reasons = assess_reresolution()
    assert required is False
    assert reasons == ()

    required, reasons = assess_reresolution(
        coverage_sufficient=False,
        sources_fresh=False,
        assurance_unchanged=False,
    )
    assert required is True
    assert reasons == (
        "coverage-insufficient",
        "source-or-binding-stale",
        "assurance-changed",
    )

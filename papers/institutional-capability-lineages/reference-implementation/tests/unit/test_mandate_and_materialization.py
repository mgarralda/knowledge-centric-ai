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
        operational_mandate={
            "authority_scope": "execution-scoped",
            "institutional_change_authority": False,
            "local_autonomy": ["reasoning", "iteration"],
            "evidence_disclosure": "evidence-contract-only",
            "registry_interaction": "reresolution-or-evidence-only",
            "reresolution_triggers": ["intent-materially-changed"],
        },
        selection={"included": ["CAP-1"], "excluded": []},
        evaluation_contract={"metrics": []},
        evidence_contract={"selection_mode": "contract-selected"},
        correctness={"mandate_bounded": True},
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

    assert materialization.delivery_mode == "access-handles"
    assert materialization.uri is None
    assert materialization.access_handles == handles
    assert materialization.preserves_assembly_semantics is True


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

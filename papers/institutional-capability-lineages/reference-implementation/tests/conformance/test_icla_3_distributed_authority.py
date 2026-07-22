from icla.specification.conformance import check_icla_3_distributed_authority


def test_assembly_mandate_preserves_cee_autonomy_without_canonical_authority():
    artifact = {
        "document_type": "contextual-assembly",
        "operational_mandate": {
            "authority_scope": "execution-scoped",
            "institutional_change_authority": False,
            "evidence_disclosure": "evidence-contract-only",
            "registry_interaction": "reresolution-or-evidence-only",
        },
        "evidence_contract": {"selection_mode": "contract-selected"},
    }

    assert check_icla_3_distributed_authority(artifact) == []

    artifact["operational_mandate"]["registry_interaction"] = "stepwise-control"
    assert "ICLA-3: mandate implies step-wise Registry control of CEE execution" in (
        check_icla_3_distributed_authority(artifact)
    )


def test_evidence_cannot_require_cee_working_state_disclosure():
    artifact = {
        "document_type": "execution-evidence-bundle",
        "execution": {
            "id": "EXE-1",
            "cee_ref": "CEE-1",
            "consumer": "CONSUMER-1",
            "local_execution": {
                "registry_stepwise_interaction": False,
                "working_state_disclosure": "contract-selected",
                "wholesale_working_state_capture": True,
            },
            "submission": {"selection_mode": "contract-selected"},
        },
        "lineage": {"assembly_ref": "ASM-1", "source_versions": ["SRC-1@1"]},
    }

    assert "ICLA-3: evidence requires wholesale CEE working-state capture" in (
        check_icla_3_distributed_authority(artifact)
    )

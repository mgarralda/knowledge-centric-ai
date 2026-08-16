from icla.specification.conformance import check_icla_10_reproducibility


def reproducible_assembly() -> dict:
    return {
        "document_type": "contextual-assembly",
        "id": "ASM-X",
        "lineage": {"cee_ref": "CEE-X"},
        "ckc_snapshot": [{"capability": "CAP-X", "ckc": "CKC-X", "version": 1}],
        "source_snapshot": [{"source": "SRC-X", "version": 1}],
        "policy_snapshot": [{"id": "POL-X", "version": 1}],
        "transformation_snapshot": [{"id": "TRANSFORM-X", "version": 1}],
        "evaluation_contract": {"id": "EVAL-X", "version": 1},
        "evidence_contract": {"id": "EVIDENCE-X", "version": 1},
        "retention": {"policy_ref": "POL-RETENTION-X"},
        "access_policy_ref": "POL-ACCESS-X",
        "materializations": [
            {
                "id": "MAT-X",
                "assembly_ref": "ASM-X",
                "cee_ref": "CEE-X",
                "content_hash": "a" * 64,
                "access": {"mode": "local-reference", "policy_ref": "POL-ACCESS-X"},
                "evaluation_binding": {"id": "EVAL-X", "version": 1},
                "evidence_binding": {"id": "EVIDENCE-X", "version": 1},
            }
        ],
    }


def test_assembly_ckcs_must_be_version_pinned():
    artifact = {
        "document_type": "contextual-assembly",
        "ckc_snapshot": [{"capability": "CAP-X", "ckc": "CKC-X"}],
    }
    assert check_icla_10_reproducibility(artifact)


def test_retained_trace_identifies_materialization_and_interpretation_bindings():
    assert check_icla_10_reproducibility(reproducible_assembly()) == []


def test_materialization_requires_hash_access_and_evaluation_evidence_bindings():
    artifact = reproducible_assembly()
    artifact["materializations"][0] = {
        "id": "MAT-X",
        "assembly_ref": "ASM-X",
        "cee_ref": "CEE-X",
        "access": {},
    }

    errors = check_icla_10_reproducibility(artifact)

    assert any("hash/access metadata" in error for error in errors)
    assert any("access metadata" in error for error in errors)
    assert any("evaluation_binding" in error for error in errors)
    assert any("evidence_binding" in error for error in errors)

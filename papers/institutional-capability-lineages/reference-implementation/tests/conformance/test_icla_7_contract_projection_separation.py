from copy import deepcopy

import pytest

from icla.specification.conformance import check_icla_7_canonical_transient_separation


def assembly_with_materialization() -> dict:
    return {
        "document_type": "contextual-assembly",
        "id": "ASM-X",
        "lineage": {"cee_ref": "CEE-X"},
        "transformation_snapshot": [{"id": "TRANSFORM-X", "version": 2}],
        "evaluation_contract": {"id": "EVAL-X", "version": 3},
        "evidence_contract": {"id": "EVIDENCE-X", "version": 4},
        "materializations": [
            {
                "id": "MAT-X",
                "assembly_ref": "ASM-X",
                "cee_ref": "CEE-X",
                "substrate": {"id": "workspace", "version": 1},
                "transformation": {"id": "TRANSFORM-X", "version": 2},
                "representation": {
                    "kind": "workspace",
                    "control": "cee-controlled",
                    "payload_retention": "policy-dependent",
                },
                "evaluation_binding": {"id": "EVAL-X", "version": 3},
                "evidence_binding": {"id": "EVIDENCE-X", "version": 4},
                "preserves_assembly_semantics": True,
                "preserves_assembly_authority": True,
            }
        ],
    }


def test_cee_side_materialization_preserves_trace_semantics_and_authority():
    assert check_icla_7_canonical_transient_separation(assembly_with_materialization()) == []


@pytest.mark.parametrize(
    ("path", "value", "message"),
    [
        (("assembly_ref",), "ASM-OTHER", "assembly or CEE traceability"),
        (("cee_ref",), "CEE-OTHER", "assembly or CEE traceability"),
        (("transformation", "version"), 99, "transformation is not version-pinned"),
        (("representation", "control"), "external", "CEE-controlled and policy-bound"),
        (("preserves_assembly_semantics",), False, "preserve assembly semantics"),
        (("preserves_assembly_authority",), False, "preserve assembly authority"),
        (("evaluation_binding", "version"), 99, "evaluation binding"),
        (("evidence_binding", "version"), 99, "evidence binding"),
    ],
)
def test_materialization_boundary_rejects_lost_trace_or_preservation(path, value, message):
    artifact = deepcopy(assembly_with_materialization())
    target = artifact["materializations"][0]
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value

    errors = check_icla_7_canonical_transient_separation(artifact)

    assert any(message in error for error in errors)

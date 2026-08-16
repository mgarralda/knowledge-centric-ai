from copy import deepcopy

import pytest

from icla.specification.conformance import check_icla_7_canonical_transient_separation


def materialization() -> dict:
    return {
        "document_type": "cee-side-materialization",
        "id": "MAT-X",
        "status": "immutable",
        "generated_from": {
            "assembly": "ASM-X",
            "cee": "CEE-X",
            "transformation": {"id": "TRANSFORM-LOCAL-X", "version": 2},
        },
        "assembly_ref": "ASM-X",
        "cee_ref": "CEE-X",
        "substrate": {"id": "workspace", "version": 1},
        "transformation": {"id": "TRANSFORM-LOCAL-X", "version": 2},
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


def test_cee_side_materialization_preserves_trace_semantics_and_authority():
    assert check_icla_7_canonical_transient_separation(materialization()) == []


def test_immutable_assembly_cannot_embed_later_materialization_records():
    errors = check_icla_7_canonical_transient_separation(
        {"document_type": "contextual-assembly", "materializations": [{"id": "MAT-X"}]}
    )

    assert errors == ["ICLA-7: an immutable assembly cannot embed later materialization records"]


@pytest.mark.parametrize(
    ("path", "value", "message"),
    [
        (("assembly_ref",), "ASM-OTHER", "provenance disagrees"),
        (("cee_ref",), "CEE-OTHER", "provenance disagrees"),
        (("transformation", "version"), None, "transformation is not version-pinned"),
        (("representation", "control"), "external", "CEE-controlled and policy-bound"),
        (("preserves_assembly_semantics",), False, "preserve assembly semantics"),
        (("preserves_assembly_authority",), False, "preserve assembly authority"),
        (("evaluation_binding", "version"), None, "evaluation_binding"),
        (("evidence_binding", "version"), None, "evidence_binding"),
    ],
)
def test_materialization_boundary_rejects_lost_trace_or_preservation(path, value, message):
    artifact = deepcopy(materialization())
    target = artifact
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value

    errors = check_icla_7_canonical_transient_separation(artifact)

    assert any(message in error for error in errors)

from icla.specification.conformance import check_icla_10_reproducibility


def test_assembly_ckcs_must_be_version_pinned():
    artifact = {
        "document_type": "contextual-assembly",
        "ckc_snapshot": [{"capability": "CAP-X", "ckc": "CKC-X"}],
    }
    assert check_icla_10_reproducibility(artifact)

from icla.specification.conformance import check_icla_6_assembly_lineage


def test_assembly_requires_complete_upstream_lineage():
    assert check_icla_6_assembly_lineage(
        {"document_type": "contextual-assembly", "lineage": {"intent_ref": "INT-X"}}
    )

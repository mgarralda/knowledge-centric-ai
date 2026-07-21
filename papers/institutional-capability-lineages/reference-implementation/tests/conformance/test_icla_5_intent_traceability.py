from icla.specification.conformance import check_icla_5_intent_traceability


def test_resolution_requires_intent_reference():
    assert check_icla_5_intent_traceability({"document_type": "capability-resolution"})

from icla.specification.conformance import check_icla_2_active_ckc


def test_active_capability_requires_versioned_ckc_pointer():
    assert check_icla_2_active_ckc(
        {"capabilities": [{"id": "CAP-X", "lifecycle": "active", "active_ckc": {}}]}
    )


def test_canonical_ckc_requires_the_complete_evaluation_contract():
    assert check_icla_2_active_ckc(
        {
            "document_type": "capability-knowledge-contract",
            "knowledge_scope": {"operational_relations": ["depends_on CAP-X"]},
            "obligations": [{"id": "OBL-1"}],
            "authorities": {"owner": "OWNER"},
            "evidence_contract": {"schema_refs": ["evidence.schema@1"]},
            "evaluation_contract": {"metrics": [{"id": "metric-without-definition"}]},
            "governance": {"immutable": True},
            "projection_rules": {"target": "CEE"},
            "source_bindings": [{"source": "SRC-1", "version": 1}],
        }
    )

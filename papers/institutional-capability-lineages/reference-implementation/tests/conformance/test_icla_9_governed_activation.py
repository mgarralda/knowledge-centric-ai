from icla.specification.conformance import check_icla_9_governed_activation


def test_unapproved_activation_is_rejected():
    assert check_icla_9_governed_activation(
        {
            "document_type": "governance-decision",
            "status": "rejected",
            "activation": {"active_pointer_transition": True},
        }
    )


def test_successor_delta_requires_a_distinct_inactive_append_record():
    errors = check_icla_9_governed_activation(
        {
            "document_type": "governance-decision",
            "id": "DEC-1",
            "status": "approved",
            "impact_record": {
                "id": "IMP-1",
                "affected_capabilities": ["CAP-1"],
                "affected_ckcs": ["CKC-1-v1", "CKC-1-v2"],
            },
            "inputs": {
                "evidence_ref": "EVD-1",
                "qualification_receipt_ref": "RCPT-1",
            },
            "successor_delta": {
                "id": "DELTA-1",
                "predecessor_ref": "CKC-1-v1",
                "successor_ref": "CKC-1-v2",
                "changed_commitments": ["evaluation_contract"],
                "rationale": "qualified evidence",
                "supporting_evidence_refs": ["EVD-1", "RCPT-1"],
                "authorization_decision_ref": "DEC-1",
                "rollback_ref": "CKC-1-v1",
                "successor_complete": True,
                "reconstruction_patch": False,
            },
        }
    )

    assert "ICLA-9: authorized successor has no distinct append record" in errors


def test_activation_must_reference_the_exact_successor_append():
    artifact = {
        "document_type": "governance-decision",
        "id": "DEC-1",
        "status": "approved",
        "impact_record": {
            "id": "IMP-1",
            "affected_capabilities": ["CAP-1"],
            "affected_ckcs": ["CKC-1-v1", "CKC-1-v2"],
        },
        "successor_delta": {
            "id": "DELTA-1",
            "predecessor_ref": "CKC-1-v1",
            "successor_ref": "CKC-1-v2",
            "changed_commitments": ["evaluation_contract"],
            "rationale": "qualified evidence",
            "supporting_evidence_refs": ["EVD-1"],
            "authorization_decision_ref": "DEC-1",
            "rollback_ref": "CKC-1-v1",
            "successor_complete": True,
            "reconstruction_patch": False,
        },
        "successor_append": {
            "id": "APPEND-1",
            "capability": "CAP-1",
            "predecessor_ref": "CKC-1-v1",
            "successor_ref": "CKC-1-v2",
            "delta_ref": "DELTA-1",
            "authorization_decision_ref": "DEC-1",
            "status": "inactive-successor",
        },
        "activation": {
            "id": "ACT-1",
            "capability": "CAP-1",
            "ckc": "CKC-1",
            "version": 2,
            "successor_append_ref": "APPEND-OTHER",
            "active_pointer_transition": {
                "from": "CKC-1-v1",
                "to": "CKC-1-v2",
            },
            "rollback_target": "CKC-1-v1",
        },
        "historical_immutability": {"retroactive_mutation": False},
    }

    assert "ICLA-9: activation does not reference the appended successor" in (
        check_icla_9_governed_activation(artifact)
    )


def test_retained_ckc_reactivation_uses_a_new_pointer_decision_without_new_append():
    artifact = {
        "document_type": "governance-decision",
        "id": "DEC-REACTIVATE-1",
        "status": "approved",
        "impact_record": {
            "id": "IMP-REACTIVATE-1",
            "affected_capabilities": ["CAP-1"],
            "affected_ckcs": ["CKC-1-v1", "CKC-1-v2"],
        },
        "activation": {
            "id": "ACT-REACTIVATE-1",
            "activation_kind": "reactivation",
            "capability": "CAP-1",
            "ckc": "CKC-1",
            "version": 1,
            "active_pointer_transition": {"from": "CKC-1-v2", "to": "CKC-1-v1"},
            "rollback_target": "CKC-1-v2",
        },
        "historical_immutability": {"retroactive_mutation": False},
    }

    assert check_icla_9_governed_activation(artifact) == []

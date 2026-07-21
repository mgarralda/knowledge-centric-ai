from icla.specification.conformance import check_icla_11_discovery_authority


def test_ordinary_decision_cannot_create_capability():
    artifact = {
        "document_type": "governance-decision",
        "capability_formation": {"new_capability_created_by_this_decision": True},
    }
    assert check_icla_11_discovery_authority(artifact)


def test_traceable_governed_promotion_can_assign_identity():
    artifact = {
        "document_type": "governance-decision",
        "capability_formation": {
            "new_capability_created_by_this_decision": True,
            "governed_promotion": {
                "proposal_ref": "PROP-1",
                "review_ref": "REV-1",
                "assigned_identity": "CAP-NEW",
                "initial_ckc_ref": "CKC-NEW@1",
            },
        },
    }
    assert not check_icla_11_discovery_authority(artifact)

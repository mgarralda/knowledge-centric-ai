from icla.specification.conformance import check_icla_11_discovery_authority


def test_ordinary_decision_cannot_create_capability():
    artifact = {
        "document_type": "governance-decision",
        "capability_formation": {"new_capability_created_by_this_decision": True},
    }
    assert check_icla_11_discovery_authority(artifact)


def test_complete_promotion_remains_outside_the_current_companion_scope():
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
    assert (
        "outside the current companion assessment scope"
        in (check_icla_11_discovery_authority(artifact)[0])
    )


def test_pre_institutional_proposal_uses_candidate_or_submitted_lifecycle_only():
    artifact = {
        "document_type": "governance-decision",
        "capability_formation": {
            "new_capability_created_by_this_decision": False,
            "proposals": [{"id": "PROP-1", "status": "proposed"}],
        },
    }

    assert check_icla_11_discovery_authority(artifact) == [
        "ICLA-11: pre-institutional proposal must be candidate or submitted"
    ]


def test_pre_institutional_proposal_cannot_carry_assigned_capability_identity():
    artifact = {
        "document_type": "governance-decision",
        "capability_formation": {
            "new_capability_created_by_this_decision": False,
            "proposals": [
                {
                    "id": "PROP-1",
                    "status": "submitted",
                    "assigned_identity": "CAP-NEW",
                }
            ],
        },
    }

    assert check_icla_11_discovery_authority(artifact) == [
        "ICLA-11: proposal carries institutional identity before promotion"
    ]

from icla.specification.conformance import check_icla_9_governed_activation


def test_unapproved_activation_is_rejected():
    assert check_icla_9_governed_activation(
        {
            "document_type": "governance-decision",
            "status": "rejected",
            "activation": {"active_pointer_transition": True},
        }
    )

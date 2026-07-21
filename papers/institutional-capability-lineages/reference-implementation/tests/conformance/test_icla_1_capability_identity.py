from icla.specification.conformance import check_icla_1_capability_identity


def test_duplicate_capability_identity_is_rejected():
    capability = {
        "id": "CAP-X",
        "name": "X",
        "outcome": "X",
        "owner": "O",
        "domain": "D",
        "lifecycle": "active",
        "active_ckc": {"id": "CKC-X", "version": 1},
    }
    assert check_icla_1_capability_identity({"capabilities": [capability, capability]})

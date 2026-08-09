from icla.specification.conformance import check_icla_5_intent_traceability


def test_resolution_requires_intent_reference():
    assert check_icla_5_intent_traceability({"document_type": "capability-resolution"})


def test_resolution_retains_matcher_version_and_confidence_semantics():
    resolution = {
        "document_type": "capability-resolution",
        "intent_ref": "INT-1",
        "cee_ref": "CEE-1",
        "cee_configuration_ref": "CEE-CONFIG-1",
        "registry_snapshot_ref": "REG-SNAP-1",
        "matcher": {
            "id": "MATCHER-1",
            "version": 1,
            "method": "hybrid",
        },
        "confidence": {
            "mode": "qualitative",
            "calibration": "not-calibrated",
        },
        "admission": {"status": "admitted", "admitted_capabilities": []},
    }

    assert not check_icla_5_intent_traceability(resolution)
    del resolution["matcher"]["version"]
    assert (
        "ICLA-5: resolution lacks matcher identity/version or confidence semantics"
        in check_icla_5_intent_traceability(resolution)
    )


def test_required_coverage_retains_method_and_versioned_reference():
    assembly = {
        "document_type": "contextual-assembly",
        "lineage": {
            "cee_ref": "CEE-1",
            "cee_configuration_ref": "CEE-CONFIG-1",
            "intent_ref": "INT-1",
            "registry_snapshot_ref": "REG-SNAP-1",
            "resolution_ref": "RES-1",
            "admission_ref": "ADM-1",
        },
        "correctness": {
            "traceable": True,
            "authorized": True,
            "required_covered": True,
            "mandate_bounded": True,
        },
        "correctness_trace": {
            "required_covered": {
                "applied_method": "deterministic",
                "applicable_reference": {
                    "kind": "validator",
                    "id": "VALIDATOR-1",
                    "version": 1,
                },
            },
            "conflicts_resolved": {
                "applicable_conflicts": [
                    {
                        "conflict_ref": "CONFLICT-1",
                        "resolution_outcome": "selected-stricter-obligation",
                        "assembly_compatible": True,
                        "policy_basis": {"id": "POL-1", "version": 1},
                    }
                ]
            },
        },
    }

    assert not check_icla_5_intent_traceability(assembly)
    del assembly["correctness_trace"]["required_covered"]["applicable_reference"][
        "version"
    ]
    assert (
        "ICLA-5: RequiredCovered trace lacks its applied method or versioned reference"
        in check_icla_5_intent_traceability(assembly)
    )
    assembly["correctness_trace"]["required_covered"]["applicable_reference"][
        "version"
    ] = 1
    del assembly["correctness_trace"]["conflicts_resolved"]["applicable_conflicts"][0][
        "policy_basis"
    ]["version"]
    assert (
        "ICLA-5: ConflictsResolved trace lacks an outcome or versioned policy basis"
        in check_icla_5_intent_traceability(assembly)
    )

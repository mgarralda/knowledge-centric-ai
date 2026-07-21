from icla.specification.conformance import (
    ConformanceChecker,
    ConformanceProfile,
    check_icla_3_distributed_authority,
    check_icla_4_registry_navigation,
    check_icla_7_canonical_transient_separation,
)


def test_profiles_are_cumulative_at_the_paper_boundaries():
    checker = ConformanceChecker()
    evidence = {
        "document_type": "execution-evidence-bundle",
        "execution": {"id": "EXE-1"},
        "lineage": {"assembly_ref": "ASM-1"},
        "measurements": {},
    }
    assert not any(
        error.startswith("ICLA-8") for error in checker.check(evidence, ConformanceProfile.CORE)
    )
    assert any(
        error.startswith("ICLA-8") for error in checker.check(evidence, ConformanceProfile.GOVERNED)
    )

    decision = {
        "document_type": "governance-decision",
        "status": "approved",
        "activation": {"active_pointer_transition": True},
        "capability_formation": {"new_capability_created_by_this_decision": True},
    }
    assert not any(
        error.startswith("ICLA-11")
        for error in checker.check(decision, ConformanceProfile.GOVERNED)
    )
    assert any(
        error.startswith("ICLA-11")
        for error in checker.check(decision, ConformanceProfile.EVOLVING)
    )


def test_missing_core_invariants_are_explicitly_checked():
    assert check_icla_3_distributed_authority({"document_type": "capability-knowledge-contract"})
    assert check_icla_4_registry_navigation(
        {
            "document_type": "institutional-capability-registry-snapshot",
            "capabilities": [],
            "relations": [{"type": "depends_on", "from": "CAP-X", "to": "CAP-Y"}],
        }
    )
    assert check_icla_7_canonical_transient_separation(
        {
            "document_type": "contextual-assembly",
            "materializations": [{"status": "canonical"}],
        }
    )

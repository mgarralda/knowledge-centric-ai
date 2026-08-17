"""ICLA-11 governed capability-formation authority checks."""

from icla.specification.conformance import (
    ConformanceChecker,
    ConformanceProfile,
    check_icla_11_formation_authority,
)


def proposal(**updates):
    value = {
        "document_type": "capability-proposal",
        "id": "PROP-1",
        "generated_from": {
            "supporting_records": [
                {
                    "record_ref": "ASM-1",
                    "record_type": "contextual-assembly",
                    "repository_ref": "ORG-MEM-1",
                    "record_locator": "assemblies/ASM-1",
                    "record_version": 1,
                    "provenance_refs": ["INT-1"],
                }
            ]
        },
        "status": "candidate",
        "proposed_responsibility": {"name": "N", "outcome": "O", "domain": "D"},
        "supporting_record_refs": ["ASM-1"],
        "recurrence_assessment": {
            "basis": "observed-recurrence",
            "justified_expectation": False,
            "declared_horizon": "future intents",
            "rationale": "One observation is insufficient",
        },
        "stable_assembly_rules": ["rule"],
        "value_assessment": {"result": "pending"},
        "comparable_outcome_refs": ["OUT-1"],
        "candidate_owner": "OWNER",
        "overlap_analysis": ["review"],
        "proposal_scoped_ckc_draft_ref": "PROP-1-CKC-DRAFT",
    }
    value.update(updates)
    return value


def promotion_decision(**updates):
    value = {
        "document_type": "governance-decision",
        "id": "DEC-1",
        "status": "approved",
        "review": {"authority": "institutional-review"},
        "capability_formation": {
            "new_capability_created_by_this_decision": True,
            "governed_promotion": {
                "proposal_ref": "PROP-1",
                "review_decision_ref": "DEC-1",
                "assigned_capability": {
                    "id": "CAP-NEW",
                    "name": "New",
                    "outcome": "Outcome",
                    "owner": "OWNER",
                    "domain": "domain",
                    "lifecycle": "approved",
                    "policy_refs": ["POL-FORMATION"],
                    "conditions": {"continuity": "approved"},
                },
                "approved_relations": [],
                "initial_ckc_ref": "CKC-NEW-v1",
            },
            "formation_append": {
                "id": "FORM-NEW-001",
                "proposal_ref": "PROP-1",
                "capability_ref": "CAP-NEW",
                "initial_ckc_ref": "CKC-NEW-v1",
                "authorization_decision_ref": "DEC-1",
                "status": "inactive-initial-ckc",
            },
        },
        "activation": {
            "id": "ACT-NEW-001",
            "activation_kind": "initial",
            "formation_append_ref": "FORM-NEW-001",
            "active_pointer_transition": {"from": None, "to": "CKC-NEW-v1"},
            "rollback_target": None,
        },
    }
    value.update(updates)
    return value


def test_incomplete_decision_cannot_create_capability():
    artifact = {
        "document_type": "governance-decision",
        "capability_formation": {"new_capability_created_by_this_decision": True},
    }
    assert check_icla_11_formation_authority(artifact)


def test_valid_positive_promotion_has_no_artifact_level_boundary_error():
    assert not check_icla_11_formation_authority(promotion_decision())

    invalid = promotion_decision()
    invalid["capability_formation"]["governed_promotion"]["approved_relations"] = [
        {"type": "depends_on", "from": "CAP-A", "to": "CAP-B"}
    ]
    assert (
        "ICLA-11: approved capability relation must involve the formed identity"
        in check_icla_11_formation_authority(invalid)
    )


def test_pre_institutional_proposal_uses_candidate_or_submitted_only():
    artifact = proposal(status="draft")
    assert check_icla_11_formation_authority(artifact) == [
        "ICLA-11: pre-institutional proposal must be candidate or submitted"
    ]


def test_pre_institutional_lifecycle_cannot_be_assigned_to_a_capability_identity():
    artifact = {
        "document_type": "institutional-capability",
        "id": "CAP-CANDIDATE",
        "lifecycle": "candidate",
    }
    assert check_icla_11_formation_authority(artifact) == [
        "ICLA-11: an institutional capability cannot use a pre-institutional lifecycle"
    ]

    registry = {
        "document_type": "institutional-capability-registry-snapshot",
        "capabilities": [artifact],
    }
    assert check_icla_11_formation_authority(registry) == [
        "ICLA-11: Registry capability uses a pre-institutional lifecycle"
    ]


def test_pre_institutional_proposal_cannot_carry_assigned_identity():
    artifact = proposal(assigned_identity="CAP-NEW")
    assert check_icla_11_formation_authority(artifact) == [
        "ICLA-11: proposal carries institutional identity before promotion"
    ]


def test_submitted_proposal_remains_valid_before_continuity_is_justified():
    artifact = proposal(status="submitted")

    assert artifact["recurrence_assessment"]["justified_expectation"] is False
    assert not check_icla_11_formation_authority(artifact)


def test_submitted_proposal_may_use_general_records_and_prospective_justification():
    supporting_records = [
        {
            "record_ref": "INT-UNRESOLVED-CUSTOMER-ONBOARDING",
            "record_type": "operational-intent",
            "repository_ref": "ORG-MEM-STRATEGY",
            "record_locator": "intents/INT-UNRESOLVED-CUSTOMER-ONBOARDING",
            "record_version": 1,
            "provenance_refs": ["CEE-CUSTOMER-ONBOARDING"],
        },
        {
            "record_ref": "DEC-STRATEGY-DIGITAL-ACCESS",
            "record_type": "strategic-decision",
            "repository_ref": "ORG-MEM-STRATEGY",
            "record_locator": "decisions/DEC-STRATEGY-DIGITAL-ACCESS",
            "record_version": 1,
            "provenance_refs": ["POL-DIGITAL-ACCESS"],
        },
        {
            "record_ref": "ONBOARD-PARTNER-PLATFORM",
            "record_type": "onboarding-record",
            "repository_ref": "ORG-MEM-STRATEGY",
            "record_locator": "onboarding/ONBOARD-PARTNER-PLATFORM",
            "record_version": 1,
            "provenance_refs": ["DEC-STRATEGY-DIGITAL-ACCESS"],
        },
    ]
    artifact = proposal(
        status="submitted",
        generated_from={"supporting_records": supporting_records},
        supporting_record_refs=[item["record_ref"] for item in supporting_records],
        recurrence_assessment={
            "basis": "prospective-continuity",
            "justified_expectation": True,
            "current_trace_sufficient": False,
            "declared_horizon": "approved two-year platform strategy",
            "rationale": (
                "The approved strategy requires the responsibility before recurrence exists"
            ),
        },
    )

    assert not check_icla_11_formation_authority(artifact)


def test_evolving_conformance_rejects_unresolved_supporting_record_provenance():
    artifact = proposal()
    artifact["generated_from"]["supporting_records"] = []

    assert ConformanceChecker().check_trace(
        [artifact], ConformanceProfile.EVOLVING
    ) == ["ICLA-11: supporting-record provenance is unresolved"]


def test_zero_one_or_multiple_proposals_remain_preinstitutional():
    assert not check_icla_11_formation_authority({"document_type": "unrelated"})
    assert not check_icla_11_formation_authority(proposal())
    assert not ConformanceChecker().check_trace(
        [proposal(), proposal(id="PROP-2")], ConformanceProfile.EVOLVING
    )


def test_proposal_draft_cannot_anticipate_an_institutional_ckc_identity():
    artifact = proposal(proposal_scoped_ckc_draft_ref="CKC-NEW-v1-draft")
    assert check_icla_11_formation_authority(artifact) == [
        "ICLA-11: proposal draft anticipates an institutional CKC identity"
    ]


def test_multiple_proposals_require_distinct_identifiers():
    errors = ConformanceChecker().check_trace(
        [proposal(), proposal()], ConformanceProfile.EVOLVING
    )
    assert "ICLA-11: crystallization proposal identifiers must be unique" in errors


def test_promotion_requires_an_authorized_review_decision():
    artifact = promotion_decision(review={})
    assert (
        "ICLA-11: promotion must reference an authorized review decision"
        in check_icla_11_formation_authority(artifact)
    )


def test_initial_activation_is_identifiable_separately_from_promotion():
    artifact = promotion_decision(
        activation={
            "id": "ACT-EMBEDDED",
            "activation_kind": "initial",
            "formation_append_ref": "FORM-OTHER",
            "active_pointer_transition": {"from": "CKC-OLD-v1", "to": "CKC-NEW-v1"},
            "rollback_target": "CKC-OLD-v1",
        }
    )
    assert (
        "ICLA-11: initial activation is not separately identifiable from promotion"
        in check_icla_11_formation_authority(artifact)
    )

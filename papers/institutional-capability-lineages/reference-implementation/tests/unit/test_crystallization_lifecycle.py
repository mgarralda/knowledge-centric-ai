"""
Institutional Capability Lineages (ICLA)
Reference Implementation

Copyright (c) 2026 Mariano Garralda-Barrio

Licensed under the MIT License.
See the LICENSE file in the repository root for details.
"""

import pytest

from icla.services.crystallization_service import CrystallizationService


def descriptor(name: str, owner: str = "institutional-governance"):
    return {
        "proposed_name": name,
        "responsibility": f"Govern recurring {name.lower()}",
        "stable_assembly_rules": [f"compose the governed {name.lower()} assembly"],
        "value_assessment": {
            "basis": "recurrent governed outcomes",
            "expected_value": "reduce repeated assembly and review effort",
        },
        "comparable_outcome_refs": [f"OUT-{name.upper().replace(' ', '-')}"],
        "candidate_owner": owner,
        "overlap_analysis": ["Flagged for Registry overlap review"],
        "draft_ckc_ref": f"CKC-{name.upper().replace(' ', '-')}-DRAFT",
    }


def test_detection_returns_an_empty_collection_when_no_pattern_reaches_threshold():
    proposals = CrystallizationService().detect_capability_proposals(
        ["SIG-A", "SIG-B"],
        candidates={"SIG-A": descriptor("Identity Migration")},
        threshold=2,
    )

    assert proposals == []


def test_detection_returns_one_proposal_for_one_distinct_recurrent_pattern():
    proposals = CrystallizationService().detect_capability_proposals(
        ["SIG-AUTH", "SIG-AUTH", "SIG-AUTH", "SIG-OTHER"],
        candidates={"SIG-AUTH": descriptor("Authentication Evolution")},
    )

    assert len(proposals) == 1
    assert proposals[0].recurrent_pattern_refs == ["SIG-AUTH"] * 3


def test_detection_preserves_multiple_independent_patterns_before_ranking():
    service = CrystallizationService()
    proposals = service.detect_capability_proposals(
        ["SIG-AUTH"] * 3 + ["SIG-COMPAT"] * 4,
        candidates={
            "SIG-AUTH": descriptor("Identity Migration"),
            "SIG-COMPAT": descriptor("Client Compatibility"),
        },
    )

    ranked = service.rank_capability_proposals(proposals)

    assert len(proposals) == 2
    assert {proposal.proposed_name for proposal in proposals} == {
        "Identity Migration",
        "Client Compatibility",
    }
    assert ranked[0].proposed_name == "Client Compatibility"
    assert service.top_capability_proposal(proposals) == ranked[0]


def test_overlapping_pattern_is_retained_for_governance_review():
    proposals = CrystallizationService().detect_capability_proposals(
        ["SIG-OVERLAP"] * 3,
        candidates={"SIG-OVERLAP": descriptor("Overlapping Responsibility")},
    )

    assert proposals[0].status == "proposed"
    assert proposals[0].overlap_analysis == ["Flagged for Registry overlap review"]


def test_proposal_requires_governed_review_before_identity_assignment():
    service = CrystallizationService()
    proposal = service.propose(
        ["SIG-AUTH", "SIG-AUTH", "SIG-AUTH"],
        proposed_name="Authentication Protocol Evolution",
        responsibility="Govern recurring authentication protocol evolution",
        stable_assembly_rules=["compose identity, API, and verification contracts"],
        value_assessment={"basis": "comparable outcomes", "expected_value": "lower risk"},
        comparable_outcome_refs=["OUT-AUTH-COMPATIBILITY"],
        candidate_owner="identity-governance",
        overlap_analysis=["Review CAP-IAM and CAP-API overlap"],
        draft_ckc_ref="CKC-AUTH-EVOL-DRAFT",
    )

    assert proposal.status == "proposed"
    assert proposal.assigned_identity is None

    under_review = service.submit_for_review(proposal, submitted_by="identity-governance")
    approved = service.decide(
        under_review,
        decision="approved",
        reviewer="institutional-governance",
        rationale="Distinct responsibility and sufficient governed evidence",
    )
    promoted = service.promote(
        approved,
        assigned_identity="CAP-AUTH-EVOL",
        initial_ckc_ref="CKC-AUTH-EVOL@1",
        authority="institutional-governance",
    )

    assert promoted.status == "promoted"
    assert promoted.assigned_identity == "CAP-AUTH-EVOL"
    assert promoted.initial_ckc_ref == "CKC-AUTH-EVOL@1"
    assert [item["to"] for item in promoted.lifecycle_history] == [
        "proposed",
        "under-review",
        "approved",
        "promoted",
    ]


def test_recurrence_score_cannot_promote_a_proposal_directly():
    proposal = CrystallizationService().propose(
        ["SIG-AUTH", "SIG-AUTH", "SIG-AUTH"],
        proposed_name="Authentication Protocol Evolution",
        responsibility="Govern recurring authentication protocol evolution",
        stable_assembly_rules=["compose identity, API, and verification contracts"],
        value_assessment={"basis": "comparable outcomes", "expected_value": "lower risk"},
        comparable_outcome_refs=["OUT-AUTH-COMPATIBILITY"],
        candidate_owner="identity-governance",
        overlap_analysis=["Review CAP-IAM and CAP-API overlap"],
        draft_ckc_ref="CKC-AUTH-EVOL-DRAFT",
    )

    with pytest.raises(ValueError, match="Only an approved proposal"):
        CrystallizationService.promote(
            proposal,
            assigned_identity="CAP-AUTH-EVOL",
            initial_ckc_ref="CKC-AUTH-EVOL@1",
            authority="institutional-governance",
        )

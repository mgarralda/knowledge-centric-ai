"""
Institutional Capability Lineages (ICLA)
Reference Implementation

Copyright (c) 2026 Mariano Garralda-Barrio

Licensed under the MIT License.
See the LICENSE file in the repository root for details.
"""

from collections import Counter
from typing import Any, Literal
from uuid import NAMESPACE_URL, uuid5

from ..models.crystallization import CapabilityProposal, ProposalStatus


class CrystallizationService:
    def detect_capability_proposals(
        self,
        signatures: list[str],
        *,
        candidates: dict[str, dict[str, Any]],
        threshold: int = 3,
    ) -> list[CapabilityProposal]:
        """Detect zero or more independent proposals without assigning authority."""
        if threshold < 1:
            raise ValueError("The recurrence threshold must be positive")
        counts = Counter(signatures)
        proposals = []
        for pattern, count in sorted(counts.items()):
            descriptor = candidates.get(pattern)
            if count < threshold or descriptor is None:
                continue
            proposal_seed = descriptor["proposed_name"] + pattern
            proposal_id = f"PROP-{str(uuid5(NAMESPACE_URL, proposal_seed)).upper()}"
            proposals.append(
                CapabilityProposal(
                    id=proposal_id,
                    recurrent_pattern_refs=[pattern] * count,
                    score=count / len(signatures),
                    lifecycle_history=[
                        {
                            "from": "detected",
                            "to": ProposalStatus.PROPOSED,
                            "authority": "pattern-detection-only",
                        }
                    ],
                    **descriptor,
                )
            )
        return proposals

    @staticmethod
    def rank_capability_proposals(
        proposals: list[CapabilityProposal],
    ) -> list[CapabilityProposal]:
        """Rank detected proposals without discarding or promoting any candidate."""
        return sorted(
            proposals,
            key=lambda proposal: (-(proposal.score or 0.0), proposal.id),
        )

    @classmethod
    def top_capability_proposal(
        cls, proposals: list[CapabilityProposal]
    ) -> CapabilityProposal | None:
        """Return the highest-ranked recommendation as a view over the full set."""
        ranked = cls.rank_capability_proposals(proposals)
        return ranked[0] if ranked else None

    def propose(
        self,
        signatures: list[str],
        *,
        proposed_name: str,
        responsibility: str,
        stable_assembly_rules: list[str],
        value_assessment: dict[str, Any],
        comparable_outcome_refs: list[str],
        candidate_owner: str,
        overlap_analysis: list[str],
        draft_ckc_ref: str,
        threshold: int = 3,
    ) -> CapabilityProposal:
        """Return the dominant recommendation while preserving set semantics in detect()."""
        counts = Counter(signatures)
        pattern, count = counts.most_common(1)[0] if counts else ("", 0)
        if count < threshold:
            raise ValueError(f"No recurrent pattern reaches threshold {threshold}")
        proposals = self.detect_capability_proposals(
            signatures,
            candidates={
                pattern: {
                    "proposed_name": proposed_name,
                    "responsibility": responsibility,
                    "stable_assembly_rules": stable_assembly_rules,
                    "value_assessment": value_assessment,
                    "comparable_outcome_refs": comparable_outcome_refs,
                    "candidate_owner": candidate_owner,
                    "overlap_analysis": overlap_analysis,
                    "draft_ckc_ref": draft_ckc_ref,
                }
            },
            threshold=threshold,
        )
        proposal = self.top_capability_proposal(proposals)
        if proposal is None:
            raise ValueError(f"No recurrent pattern reaches threshold {threshold}")
        return proposal

    @staticmethod
    def submit_for_review(
        proposal: CapabilityProposal, *, submitted_by: str
    ) -> CapabilityProposal:
        if proposal.status != ProposalStatus.PROPOSED:
            raise ValueError("Only a proposed capability can enter institutional review")
        return CrystallizationService._transition(
            proposal,
            ProposalStatus.UNDER_REVIEW,
            authority=submitted_by,
        )

    @staticmethod
    def decide(
        proposal: CapabilityProposal,
        *,
        decision: Literal["approved", "rejected"],
        reviewer: str,
        rationale: str,
    ) -> CapabilityProposal:
        if proposal.status != ProposalStatus.UNDER_REVIEW:
            raise ValueError("Only a proposal under review can be decided")
        return CrystallizationService._transition(
            proposal,
            ProposalStatus(decision),
            authority=reviewer,
            rationale=rationale,
        )

    @staticmethod
    def promote(
        proposal: CapabilityProposal,
        *,
        assigned_identity: str,
        initial_ckc_ref: str,
        authority: str,
    ) -> CapabilityProposal:
        if proposal.status != ProposalStatus.APPROVED:
            raise ValueError("Only an approved proposal can assign institutional identity")
        return CrystallizationService._transition(
            proposal,
            ProposalStatus.PROMOTED,
            authority=authority,
            assigned_identity=assigned_identity,
            initial_ckc_ref=initial_ckc_ref,
        )

    @staticmethod
    def _transition(
        proposal: CapabilityProposal,
        status: ProposalStatus,
        *,
        authority: str,
        rationale: str | None = None,
        **updates,
    ) -> CapabilityProposal:
        transition = {
            "from": proposal.status,
            "to": status,
            "authority": authority,
        }
        if rationale:
            transition["rationale"] = rationale
        return CapabilityProposal.model_validate(
            {
                **proposal.model_dump(mode="python"),
                **updates,
                "status": status,
                "lifecycle_history": [*proposal.lifecycle_history, transition],
            }
        )

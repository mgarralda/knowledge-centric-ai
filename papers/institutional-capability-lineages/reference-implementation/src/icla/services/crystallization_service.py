"""
Institutional Capability Lineages (ICLA)
Reference Implementation

Copyright (c) 2026 Mariano Garralda-Barrio

Licensed under the MIT License.
See the LICENSE file in the repository root for details.
"""

from collections import Counter
from typing import Literal
from uuid import NAMESPACE_URL, uuid5

from ..models.crystallization import CapabilityProposal, ProposalStatus


class CrystallizationService:
    def propose(
        self,
        signatures: list[str],
        *,
        proposed_name: str,
        responsibility: str,
        threshold: int = 3,
        candidate_owner: str | None = None,
    ) -> CapabilityProposal:
        counts = Counter(signatures)
        pattern, count = counts.most_common(1)[0] if counts else ("", 0)
        if count < threshold:
            raise ValueError(f"No recurrent pattern reaches threshold {threshold}")
        return CapabilityProposal(
            id=f"PROP-{str(uuid5(NAMESPACE_URL, proposed_name + pattern)).upper()}",
            recurrent_pattern_refs=[pattern] * count,
            proposed_name=proposed_name,
            responsibility=responsibility,
            candidate_owner=candidate_owner,
            overlap_analysis=["Requires governance review against the Registry"],
            score=count / len(signatures),
            lifecycle_history=[
                {
                    "from": "detected",
                    "to": ProposalStatus.PROPOSED,
                    "authority": "pattern-detection-only",
                }
            ],
        )

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

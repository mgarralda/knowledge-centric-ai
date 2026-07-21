"""
Institutional Capability Lineages (ICLA)
Reference Implementation

Copyright (c) 2026 Mariano Garralda-Barrio

Licensed under the MIT License.
See the LICENSE file in the repository root for details.
"""

# Module purpose: Record declared human/institutional decisions; never synthesize approval.

from ..exceptions import AuthorizationError
from ..models.governance import GovernanceDecision
from ..repositories.governance_repository import GovernanceRepository


class GovernanceService:
    def __init__(self, repository: GovernanceRepository) -> None:
        self.repository = repository

    def adjudicate(
        self, decision: GovernanceDecision, *, reviewer: str, policy_refs: list[str]
    ) -> GovernanceDecision:
        declared_reviewer = (
            decision.review.get("reviewer")
            or decision.review.get("reviewer_id")
            or decision.review.get("authority")
        )
        if declared_reviewer and declared_reviewer != reviewer:
            raise AuthorizationError("Reviewer does not match the declared governance decision")
        if not policy_refs:
            raise AuthorizationError("Adjudication requires explicit policy references")
        self.repository.append_decision(decision)
        return decision

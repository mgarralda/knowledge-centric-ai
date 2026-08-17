"""
Institutional Capability Lineage Architecture (ICLA)
Reference Implementation

Copyright (c) 2026 Mariano Garralda-Barrio

Licensed under the MIT License.
See the LICENSE file in the repository root for details.
"""

# Module purpose: Record declared institutional decisions; never synthesize approval.

from ..exceptions import AuthorizationError
from ..models.governance import GovernanceDecision
from ..repositories.governance_repository import GovernanceRepository


class GovernanceService:
    def __init__(self, repository: GovernanceRepository) -> None:
        self.repository = repository

    def adjudicate(
        self,
        decision: GovernanceDecision,
        *,
        decision_actor: str,
        policy_refs: list[str],
    ) -> GovernanceDecision:
        declared_decision_actor = (
            decision.review.get("decision_actor")
            or decision.review.get("authority")
            or decision.review.get("reviewer")
            or decision.review.get("reviewer_id")
        )
        if declared_decision_actor and declared_decision_actor != decision_actor:
            raise AuthorizationError(
                "Decision actor does not match the declared governance authority"
            )
        if not policy_refs:
            raise AuthorizationError("Adjudication requires explicit policy references")
        self.repository.append_decision(decision)
        return decision

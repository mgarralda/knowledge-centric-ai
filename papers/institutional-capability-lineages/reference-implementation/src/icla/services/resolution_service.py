"""
Institutional Capability Lineages (ICLA)
Reference Implementation

Copyright (c) 2026 Mariano Garralda-Barrio

Licensed under the MIT License.
See the LICENSE file in the repository root for details.
"""

# Module purpose: Deterministic candidate generation, graph expansion, and constraint validation.

from __future__ import annotations

from uuid import NAMESPACE_URL, uuid5

from ..models.intent import Intent
from ..models.registry import RegistrySnapshot
from ..models.resolution import AdmissionDecision, ResolutionResult
from ..policies.assurance import assurance_satisfies
from ..policies.authorization import can_consume
from ..policies.freshness import is_fresh
from ..policies.outcome_coverage import (
    outcome_matches,
    semantic_terms,
    structured_text_values,
)
from .registry_service import RegistryService

MANDATORY_EXPANSION_RELATIONS = {"depends_on"}
ADVISORY_RELATIONS = {"specializes", "composes_with", "shares_knowledge"}
CONFLICT_RELATIONS = {"conflicts_with"}


def _identifier(prefix: str, seed: str) -> str:
    return f"{prefix}-{str(uuid5(NAMESPACE_URL, seed)).upper()}"


class ResolutionService:
    def resolve_intent(self, intent: Intent, registry: RegistrySnapshot) -> ResolutionResult:
        required = set(intent.required_outcomes)
        intent_terms = semantic_terms(
            intent.goal,
            *intent.required_outcomes,
            *structured_text_values(intent.context),
        )
        candidates = []
        for capability in registry.capabilities:
            matches = [value for value in required if outcome_matches(value, capability.outcome)]
            capability_terms = semantic_terms(
                capability.name,
                capability.outcome,
                capability.domain,
            )
            shared_terms = sorted(intent_terms & capability_terms)
            if matches or shared_terms:
                candidates.append(
                    {
                        "capability": capability.id,
                        "score": (len(matches) + len(shared_terms))
                        / (len(required) + len(intent_terms)),
                        "rationale": [
                            *[f"matched required outcome: {value}" for value in matches],
                            *[f"matched intent concept: {value}" for value in shared_terms],
                        ],
                    }
                )
        service = RegistryService(registry)
        seed_ids = {item["capability"] for item in candidates}
        traversed, expanded = [], set(seed_ids)
        pending = list(seed_ids)
        dependency_ids: set[str] = set()
        while pending:
            capability_id = pending.pop()
            related, relations = service.related(
                capability_id,
                relation_types=MANDATORY_EXPANSION_RELATIONS,
            )
            traversed.extend(item.model_dump(by_alias=True) for item in relations)
            for item in related:
                dependency_ids.add(item.id)
                if item.id not in expanded:
                    expanded.add(item.id)
                    pending.append(item.id)

        advisory_relations = [
            relation.model_dump(by_alias=True)
            for capability_id in sorted(expanded)
            for relation in service.relations_from(
                capability_id,
                relation_types=ADVISORY_RELATIONS,
            )
        ]
        admitted, excluded, validations = [], [], []
        for capability_id in sorted(expanded):
            capability = registry.capability(capability_id)
            if capability is None:
                continue
            authorized, rationale = can_consume(intent.consumer, capability)
            active = capability.lifecycle.value == "active"
            fresh, freshness_rationale = is_fresh(getattr(capability, "expires_at", None))
            offered_assurance = getattr(capability, "assurance", None)
            required_assurance = intent.assurance.get("level")
            assurance_ok, assurance_rationale = (
                assurance_satisfies(str(offered_assurance), str(required_assurance))
                if offered_assurance and required_assurance
                else (True, "capability does not declare a separate assurance level")
            )
            passed = authorized and active and fresh and assurance_ok
            validations.append(
                {
                    "capability": capability_id,
                    "authorized": authorized,
                    "active": active,
                    "fresh": fresh,
                    "assurance_compatible": assurance_ok,
                    "passed": passed,
                    "rationale": [rationale, freshness_rationale, assurance_rationale],
                }
            )
            if passed:
                admitted.append(
                    {
                        "capability": capability.id,
                        "ckc": capability.active_ckc.id,
                        "version": capability.active_ckc.version,
                    }
                )
            else:
                excluded.append(
                    {
                        "capability": capability_id,
                        "reasons": [
                            reason
                            for condition, reason in (
                                (authorized, rationale),
                                (active, "capability is not active"),
                                (fresh, freshness_rationale),
                                (assurance_ok, assurance_rationale),
                            )
                            if not condition
                        ],
                    }
                )

        admitted_ids = {item["capability"] for item in admitted}
        covered_outcomes = {
            outcome
            for outcome in required
            if any(
                capability and outcome_matches(outcome, capability.outcome)
                for capability_id in admitted_ids
                if (capability := registry.capability(capability_id))
            )
        }
        missing_outcomes = required - covered_outcomes
        missing_dependencies = dependency_ids - admitted_ids
        conflicts = [
            relation.model_dump(by_alias=True)
            for capability_id in sorted(admitted_ids)
            for relation in service.relations_from(
                capability_id,
                relation_types=CONFLICT_RELATIONS,
            )
            if relation.target in admitted_ids
        ]
        budget_limit = intent.budget.get("max_capabilities")
        within_budget = budget_limit is None or len(admitted) <= int(budget_limit)
        authoritative = (
            bool(admitted)
            and not missing_outcomes
            and not missing_dependencies
            and not conflicts
            and within_budget
        )
        status = "admitted" if authoritative else "partial" if admitted else "inadmissible"
        resolution_id = _identifier("RES", f"{intent.id}:{registry.id}")
        return ResolutionResult(
            id=resolution_id,
            schema_ref="schemas/resolution.schema.yaml",
            generated_from={"intent": intent.id, "registry_snapshot": registry.id},
            cee_ref=str(intent.cee["id"]),
            intent_ref=intent.id,
            registry_snapshot_ref=registry.id,
            candidate_generation={"candidates": candidates},
            relation_expansion={
                "capabilities": sorted(expanded),
                "mandatory_relations": traversed,
                "advisory_relations": advisory_relations,
            },
            filtering={
                "excluded": excluded,
                "missing_outcomes": sorted(missing_outcomes),
                "missing_dependencies": sorted(missing_dependencies),
                "within_budget": within_budget,
            },
            constraint_validation=validations or [{"passed": False, "rationale": "no candidates"}],
            conflict_resolution={
                "status": "unresolved" if conflicts else "not-required",
                "conflicts": conflicts,
                "rationale": (
                    ["simultaneously admitted capabilities require governance review"]
                    if conflicts
                    else []
                ),
            },
            admission=AdmissionDecision(
                id=_identifier("ADM", resolution_id),
                status=status,
                admitted_capabilities=admitted,
                rationale=[
                    f"covered outcomes: {sorted(covered_outcomes)}",
                    f"missing outcomes: {sorted(missing_outcomes)}",
                    f"missing mandatory dependencies: {sorted(missing_dependencies)}",
                    f"within budget: {within_budget}",
                ],
            ),
            trace={"algorithm": "icla-reference-deterministic-v1"},
        )

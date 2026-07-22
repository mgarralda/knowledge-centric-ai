"""
Institutional Capability Lineages (ICLA)
Reference Implementation

Copyright (c) 2026 Mariano Garralda-Barrio

Licensed under the MIT License.
See the LICENSE file in the repository root for details.
"""

# Module purpose: Build immutable assemblies only when all correctness conditions pass.

from __future__ import annotations

from uuid import NAMESPACE_URL, uuid5

from ..exceptions import AdmissionError
from ..models.assembly import Assembly
from ..models.ckc import CapabilityKnowledgeContract
from ..models.intent import Intent
from ..models.registry import RegistrySnapshot
from ..models.resolution import ResolutionResult
from ..policies.conflict_resolution import resolve_obligation_conflicts
from ..policies.outcome_coverage import outcome_matches


def _ckc_outcomes(ckc: CapabilityKnowledgeContract) -> set[str]:
    declared = ckc.knowledge_scope.get("outcomes", [])
    if isinstance(declared, str):
        declared = [declared]
    return {str(value) for value in declared}


class AssemblyService:
    def assemble(
        self,
        intent: Intent,
        resolution: ResolutionResult,
        registry_snapshot: RegistrySnapshot,
        ckcs: list[CapabilityKnowledgeContract],
        policies: list[str] | None = None,
    ) -> Assembly:
        if resolution.admission.status != "admitted":
            raise AdmissionError(
                "Only an admitted resolution can produce an authoritative assembly"
            )
        admitted = {
            (item.capability, item.ckc, item.version)
            for item in resolution.admission.admitted_capabilities
        }
        supplied = {(item.capability_ref, item.id, item.version) for item in ckcs}
        exact = admitted == supplied
        obligations, conflict_rationale, unresolved_obligations = resolve_obligation_conflicts(
            [item for ckc in ckcs for item in ckc.obligations]
        )
        metrics = [metric for ckc in ckcs for metric in ckc.evaluation_contract.get("metrics", [])]
        budget_limit = intent.budget.get("max_capabilities")
        within_budget = budget_limit is None or len(ckcs) <= int(budget_limit)
        admitted_ids = {item[0] for item in admitted}
        offered_outcomes = {
            capability.outcome
            for capability_id in admitted_ids
            if (capability := registry_snapshot.capability(capability_id)) is not None
        }
        for ckc in ckcs:
            offered_outcomes.update(_ckc_outcomes(ckc))
        missing_outcomes = {
            required
            for required in intent.required_outcomes
            if not any(outcome_matches(required, offered) for offered in offered_outcomes)
        }
        admitted_validations = [
            item
            for item in resolution.constraint_validation
            if item.get("capability") in admitted_ids
        ]
        resolution_conflicts = resolution.conflict_resolution.get("conflicts", [])
        correctness = {
            "traceable": resolution.intent_ref == intent.id
            and resolution.registry_snapshot_ref == registry_snapshot.id,
            "authorized": bool(admitted_validations)
            and all(item.get("authorized") for item in admitted_validations),
            "required_covered": not missing_outcomes,
            "evaluation_bound": bool(metrics),
            "conflicts_resolved": not unresolved_obligations and not resolution_conflicts,
            "within_budget": within_budget,
            "mandate_bounded": True,
        }
        failed = [name for name, value in correctness.items() if not value]
        if not exact:
            failed.append("exact_ckc_snapshot")
        if failed:
            raise AdmissionError(f"Assembly correctness failed: {', '.join(failed)}")
        seed = f"{intent.id}:{resolution.id}:" + ",".join(f"{c.id}@{c.version}" for c in ckcs)
        identifier = f"ASM-{str(uuid5(NAMESPACE_URL, seed)).upper()}"
        return Assembly(
            id=identifier,
            schema_ref="schemas/assembly.schema.yaml",
            generated_from={
                "intent": intent.id,
                "resolution": resolution.id,
                "registry": registry_snapshot.id,
                "algorithm": "icla-reference-deterministic-v1",
            },
            lineage={
                "cee_ref": str(intent.cee["id"]),
                "intent_ref": intent.id,
                "registry_snapshot_ref": registry_snapshot.id,
                "resolution_ref": resolution.id,
                "admission_ref": resolution.admission.id,
            },
            ckc_snapshot=[
                {"capability": c.capability_ref, "ckc": c.id, "version": c.version} for c in ckcs
            ],
            source_snapshot=[binding for c in ckcs for binding in c.source_bindings],
            policy_snapshot=[
                {"id": policy_ref, "version": 1} for policy_ref in (policies or [])
            ]
            or [{"id": "POL-ICLA-DEFAULT-ASSEMBLY", "version": 1}],
            transformation_snapshot=[
                {"id": "TRANSFORM-ICLA-REFERENCE-ASSEMBLY", "version": 1}
            ],
            operational_mandate={
                "authority_scope": "execution-scoped",
                "institutional_change_authority": False,
                "local_autonomy": [
                    "reasoning",
                    "planning",
                    "working-memory",
                    "local-stores",
                    "tool-use",
                    "coordination",
                    "iteration",
                ],
                "evidence_disclosure": "evidence-contract-only",
                "registry_interaction": "reresolution-or-evidence-only",
                "reresolution_triggers": [
                    "intent-materially-changed",
                    "coverage-insufficient",
                    "authority-invalid",
                    "source-or-binding-stale",
                    "risk-changed",
                    "assurance-changed",
                ],
            },
            selection={
                "included": sorted(item[0] for item in admitted),
                "excluded": resolution.filtering.get("excluded", []),
                "obligations": obligations,
                "conflict_rationale": conflict_rationale,
                "unresolved_conflicts": unresolved_obligations + resolution_conflicts,
                "covered_outcomes": sorted(offered_outcomes),
                "missing_outcomes": sorted(missing_outcomes),
                "policy_refs": policies or [],
            },
            evaluation_contract={
                "id": "EVAL-ICLA-REFERENCE-ASSEMBLY",
                "version": 1,
                "metrics": metrics,
            },
            evidence_contract={
                "contracts": [c.evidence_contract for c in ckcs],
                "selection_mode": "contract-selected",
                "working_state_disclosure": "prohibited-unless-contract-required",
                "checkpoint_policy": ["terminal", "contract-defined"],
            },
            correctness=correctness,
            retention={
                "policy_ref": "POL-ICLA-TRACE-RETENTION-v1",
                "historical_reproduction": "required",
            },
            access_policy_ref="POL-ICLA-TRACE-ACCESS-v1",
            materializations=[
                {
                    "substrate": "logical",
                    "delivery_mode": "logical",
                    "preserves_assembly_semantics": True,
                    "status": "available",
                }
            ],
        )

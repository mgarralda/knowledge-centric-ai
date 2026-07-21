"""
Institutional Capability Lineages (ICLA)
Reference Implementation

Copyright (c) 2026 Mariano Garralda-Barrio

Licensed under the MIT License.
See the LICENSE file in the repository root for details.
"""

# Module purpose: Executable checks for the paper's architectural invariants.

from __future__ import annotations

from collections.abc import Callable, Iterable
from enum import StrEnum
from typing import Any

from ..exceptions import ConformanceError


class ConformanceProfile(StrEnum):
    CORE = "ICLA-Core"
    GOVERNED = "ICLA-Governed"
    EVOLVING = "ICLA-Evolving"


def _missing(mapping: dict[str, Any], fields: Iterable[str]) -> list[str]:
    return [field for field in fields if mapping.get(field) in (None, "", [], {})]


def _passed(value: Any) -> bool:
    return value is True or str(value).casefold() in {"pass", "passed", "success"}


def check_icla_1_capability_identity(registry: dict[str, Any]) -> list[str]:
    """Active capabilities have stable identity, ownership, lifecycle, and an active pointer."""
    if registry.get("document_type") not in {
        "institutional-capability-registry-snapshot",
        None,
    }:
        return []
    capabilities = registry.get("capabilities", [])
    ids = [item.get("id") for item in capabilities]
    errors = ["ICLA-1: capability identifiers must be unique"] if len(ids) != len(set(ids)) else []
    for item in capabilities:
        if item.get("lifecycle") != "active":
            continue
        missing = _missing(item, ("id", "owner", "lifecycle", "active_ckc"))
        pointer_missing = _missing(item.get("active_ckc", {}), ("id", "version"))
        if missing or pointer_missing:
            errors.append(
                f"ICLA-1: active capability {item.get('id', '<unknown>')} lacks "
                f"identity fields {sorted(set(missing + pointer_missing))}"
            )
    return errors


def check_icla_2_active_ckc(artifact: dict[str, Any]) -> list[str]:
    """Active pointers are versioned and CKC artifacts contain the canonical contract."""
    document_type = artifact.get("document_type")
    if document_type in {"institutional-capability-registry-snapshot", None}:
        return [
            f"ICLA-2: {item.get('id')} has no versioned active CKC pointer"
            for item in artifact.get("capabilities", [])
            if item.get("lifecycle") == "active"
            and _missing(item.get("active_ckc", {}), ("id", "version"))
        ]
    if document_type != "capability-knowledge-contract":
        return []

    errors: list[str] = []
    contract_fields = (
        "knowledge_scope",
        "obligations",
        "authorities",
        "evidence_contract",
        "evaluation_contract",
        "governance",
        "projection_rules",
        "source_bindings",
    )
    missing = _missing(artifact, contract_fields)
    if missing:
        errors.append(f"ICLA-2: CKC canonical contract misses {missing}")
    if not artifact.get("knowledge_scope", {}).get("operational_relations"):
        errors.append("ICLA-2: CKC has no declared operational relations")
    if not artifact.get("evidence_contract", {}).get("schema_refs"):
        errors.append("ICLA-2: CKC has no governed evidence schema reference")
    metrics = artifact.get("evaluation_contract", {}).get("metrics", [])
    if not metrics:
        errors.append("ICLA-2: CKC evaluation contract has no applicable metrics")
    for metric in metrics:
        metric_missing = _missing(
            metric,
            (
                "id",
                "unit",
                "collection_condition",
                "threshold",
                "interpretation_rule",
                "representative_case_basis",
            ),
        )
        if metric_missing:
            errors.append(
                f"ICLA-2: metric {metric.get('id', '<unknown>')} misses {metric_missing}"
            )
    if artifact.get("governance", {}).get("immutable") is not True:
        errors.append("ICLA-2: CKC version is not declared immutable")
    return errors


def check_icla_3_distributed_authority(artifact: dict[str, Any]) -> list[str]:
    """CEE contributions enter through identified source or evidence paths."""
    document_type = artifact.get("document_type")
    if document_type == "capability-knowledge-contract":
        errors = []
        if not artifact.get("source_bindings"):
            errors.append("ICLA-3: CKC has no identified source bindings")
        if not artifact.get("authorities") or not artifact.get("governance"):
            errors.append("ICLA-3: CKC has no governed authority declaration")
        return errors
    if document_type == "execution-evidence-bundle":
        errors = []
        execution = artifact.get("execution", {})
        if _missing(execution, ("id", "cee_ref", "consumer")):
            errors.append("ICLA-3: evidence has no originating execution and CEE consumer")
        if _missing(artifact.get("lineage", {}), ("assembly_ref", "source_versions")):
            errors.append("ICLA-3: evidence has no identified governed submission path")
        if artifact.get("canonical_mutation") is True:
            errors.append("ICLA-3: a CEE contribution cannot directly mutate canonical state")
        return errors
    return []


def check_icla_4_registry_navigation(registry: dict[str, Any]) -> list[str]:
    """Registry entries support metadata, lifecycle, policy, condition, and relation navigation."""
    if registry.get("document_type") != "institutional-capability-registry-snapshot":
        return []
    capabilities = registry.get("capabilities", [])
    capability_ids = {item.get("id") for item in capabilities}
    errors = []
    for item in capabilities:
        missing = _missing(
            item,
            ("id", "domain", "lifecycle", "owner", "active_ckc", "policy_refs", "conditions"),
        )
        if missing:
            errors.append(
                f"ICLA-4: capability {item.get('id', '<unknown>')} is not filterable by {missing}"
            )
    for relation in registry.get("relations", []):
        relation_type = relation.get("type")
        source = relation.get("from")
        target = relation.get("to")
        if not relation_type:
            errors.append("ICLA-4: Registry relation has no type")
        if source not in capability_ids or target not in capability_ids:
            errors.append(f"ICLA-4: relation {source!r} -> {target!r} has an unknown endpoint")
    return errors


def check_icla_5_intent_traceability(artifact: dict[str, Any]) -> list[str]:
    document_type = artifact.get("document_type")
    if document_type == "capability-resolution":
        errors = []
        missing = _missing(
            artifact,
            ("cee_ref", "intent_ref", "registry_snapshot_ref", "admission"),
        )
        if missing:
            errors.append(f"ICLA-5: resolution misses trace fields {missing}")
        if artifact.get("admission", {}).get("status") == "admitted":
            failed = [
                item.get("constraint", "<unknown>")
                for item in artifact.get("constraint_validation", [])
                if not _passed(item.get("result", item.get("passed")))
            ]
            if failed:
                errors.append(f"ICLA-5: admitted resolution has failed constraints {failed}")
        return errors
    if document_type == "contextual-assembly":
        errors = []
        missing = _missing(
            artifact.get("lineage", {}),
            ("cee_ref", "intent_ref", "registry_snapshot_ref", "resolution_ref", "admission_ref"),
        )
        if missing:
            errors.append(f"ICLA-5: assembly misses execution trace fields {missing}")
        correctness = artifact.get("correctness", {})
        required = ("traceable", "authorized", "required_covered")
        failed = [name for name in required if correctness.get(name) is not True]
        if failed:
            errors.append(f"ICLA-5: authoritative assembly fails {failed}")
        return errors
    return []


def check_icla_6_assembly_lineage(artifact: dict[str, Any]) -> list[str]:
    if artifact.get("document_type") != "contextual-assembly":
        return []
    errors = []
    lineage_missing = _missing(
        artifact.get("lineage", {}),
        ("cee_ref", "intent_ref", "registry_snapshot_ref", "resolution_ref", "admission_ref"),
    )
    if lineage_missing:
        errors.append(f"ICLA-6: assembly lineage misses {lineage_missing}")
    snapshots = (
        ("CKC", artifact.get("ckc_snapshot", []), ("capability", "ckc", "version")),
        ("source", artifact.get("source_snapshot", []), ("source", "version")),
        ("policy", artifact.get("policy_snapshot", []), ("id", "version")),
        (
            "transformation",
            artifact.get("transformation_snapshot", []),
            ("id", "version"),
        ),
    )
    for label, values, fields in snapshots:
        if not values or any(_missing(value, fields) for value in values):
            errors.append(f"ICLA-6: assembly lacks exact {label} versions")
    evaluation = artifact.get("evaluation_contract", {})
    if _missing(evaluation, ("id", "version", "metrics")) or any(
        not metric.get("authority") for metric in evaluation.get("metrics", [])
    ):
        errors.append("ICLA-6: assembly lacks exact evaluation-contract lineage")
    return errors


def check_icla_7_canonical_transient_separation(artifact: dict[str, Any]) -> list[str]:
    if artifact.get("document_type") == "capability-knowledge-contract":
        generated_from = artifact.get("generated_from", {})
        if generated_from.get("materialization") or generated_from.get("materialization_ref"):
            return ["ICLA-7: a materialization cannot silently become a canonical CKC"]
    if artifact.get("document_type") != "contextual-assembly":
        return []
    return [
        "ICLA-7: a consumer materialization cannot be marked canonical"
        for item in artifact.get("materializations", [])
        if item.get("canonical") is True
        or item.get("status") in {"canonical", "canonical-approved", "active"}
    ]


def check_icla_8_evidence_separation(artifact: dict[str, Any]) -> list[str]:
    if artifact.get("document_type") != "execution-evidence-bundle":
        return []
    errors = []
    measurements = artifact.get("measurements", {})
    missing = [name for name in ("governed", "nonstandard") if name not in measurements]
    if missing:
        errors.append(f"ICLA-8: evidence measurements miss {missing}")
        return errors
    for metric in measurements.get("governed", []):
        if _missing(metric, ("metric_id", "governed_definition")):
            errors.append("ICLA-8: governed measurement lacks its governed definition")
    for metric in measurements.get("nonstandard", []):
        if metric.get("institutional_comparison") != "excluded":
            errors.append("ICLA-8: non-standard measurement is not excluded from comparison")
        if metric.get("threshold_decision_use") != "prohibited":
            errors.append("ICLA-8: non-standard measurement can influence a threshold decision")
    if artifact.get("status") in {"qualified-for-review", "adjudicated"} and not artifact.get(
        "gateway_receipt"
    ):
        errors.append("ICLA-8: qualified evidence has no gateway receipt")
    return errors


def check_icla_9_governed_activation(artifact: dict[str, Any]) -> list[str]:
    if artifact.get("document_type") != "governance-decision":
        return []
    activation = artifact.get("activation", {})
    if not activation:
        return []
    errors = []
    if artifact.get("status") != "approved":
        errors.append("ICLA-9: activation requires an approved governance decision")
    if _missing(
        artifact.get("impact_record", {}),
        ("id", "affected_capabilities", "affected_ckcs"),
    ):
        errors.append("ICLA-9: canonical change has no impact record")
    if _missing(activation, ("id", "capability", "ckc", "version", "active_pointer_transition")):
        errors.append("ICLA-9: activation target is incomplete")
    transition = activation.get("active_pointer_transition")
    if not isinstance(transition, dict) or _missing(transition, ("from", "to")):
        errors.append("ICLA-9: activation does not declare the exact pointer transition")
    if artifact.get("historical_immutability", {}).get("retroactive_mutation") is not False:
        errors.append("ICLA-9: activation does not preserve historical state")
    return errors


def check_icla_10_reproducibility(artifact: dict[str, Any]) -> list[str]:
    if artifact.get("document_type") != "contextual-assembly":
        return []
    errors = []
    if not artifact.get("ckc_snapshot") or any(
        _missing(item, ("capability", "ckc", "version"))
        for item in artifact.get("ckc_snapshot", [])
    ):
        errors.append("ICLA-10: assembly CKC references are not version-pinned")
    for field in ("source_snapshot", "policy_snapshot", "transformation_snapshot"):
        if not artifact.get(field):
            errors.append(f"ICLA-10: assembly has no retained {field}")
    if _missing(artifact.get("evaluation_contract", {}), ("id", "version")):
        errors.append("ICLA-10: measurement interpretation contract is not version-pinned")
    if not artifact.get("retention", {}).get("policy_ref") or not artifact.get(
        "access_policy_ref"
    ):
        errors.append("ICLA-10: assembly lacks retention or access policy metadata")
    return errors


def check_icla_11_discovery_authority(artifact: dict[str, Any]) -> list[str]:
    if artifact.get("document_type") != "governance-decision":
        return []
    formation = artifact.get("capability_formation", {})
    if formation.get("new_capability_created_by_this_decision") is not True:
        return []
    promotion = formation.get("governed_promotion", {})
    missing = _missing(
        promotion,
        ("proposal_ref", "review_ref", "assigned_identity", "initial_ckc_ref"),
    )
    return (
        [f"ICLA-11: capability identity lacks governed, traceable promotion fields {missing}"]
        if missing
        else []
    )


class ConformanceChecker:
    _core: tuple[Callable[[dict[str, Any]], list[str]], ...] = (
        check_icla_1_capability_identity,
        check_icla_2_active_ckc,
        check_icla_3_distributed_authority,
        check_icla_4_registry_navigation,
        check_icla_5_intent_traceability,
        check_icla_6_assembly_lineage,
        check_icla_7_canonical_transient_separation,
        check_icla_10_reproducibility,
    )
    _governed = _core + (
        check_icla_8_evidence_separation,
        check_icla_9_governed_activation,
    )
    _evolving = _governed + (check_icla_11_discovery_authority,)

    def check(
        self, artifact: dict[str, Any], profile: ConformanceProfile = ConformanceProfile.CORE
    ) -> list[str]:
        checks_by_profile = {
            ConformanceProfile.CORE: self._core,
            ConformanceProfile.GOVERNED: self._governed,
            ConformanceProfile.EVOLVING: self._evolving,
        }
        return [error for check in checks_by_profile[profile] for error in check(artifact)]

    def require(
        self, artifact: dict[str, Any], profile: ConformanceProfile = ConformanceProfile.CORE
    ) -> None:
        errors = self.check(artifact, profile)
        if errors:
            raise ConformanceError("\n".join(errors))

    def check_trace(
        self,
        artifacts: Iterable[dict[str, Any]],
        profile: ConformanceProfile = ConformanceProfile.CORE,
    ) -> list[str]:
        """Check invariants plus cross-artifact identity and version continuity."""
        values = list(artifacts)
        errors = [error for artifact in values for error in self.check(artifact, profile)]
        by_type = {artifact.get("document_type"): artifact for artifact in values}
        intent = by_type.get("operational-intent", {})
        resolution = by_type.get("capability-resolution", {})
        assembly = by_type.get("contextual-assembly", {})
        evidence = by_type.get("execution-evidence-bundle", {})
        decision = by_type.get("governance-decision", {})

        if intent:
            cee_id = intent.get("cee", {}).get("id")
            downstream_cee_refs = {
                resolution.get("cee_ref"),
                assembly.get("lineage", {}).get("cee_ref"),
                evidence.get("execution", {}).get("cee_ref"),
            }
            if downstream_cee_refs - {None, cee_id}:
                errors.append("ICLA-5: CEE identity changes across the execution trace")

        if evidence:
            execution = evidence.get("execution", {})
            candidates = evidence.get("candidate_knowledge", [])
            if candidates and execution.get("produced_knowledge", {}).get(
                "institutional_authority"
            ) is not False:
                errors.append(
                    "ICLA-3/8: CEE-produced knowledge must remain non-authoritative"
                )
            for candidate in candidates:
                if candidate.get("produced_by") != execution.get("cee_ref"):
                    errors.append("ICLA-3: candidate knowledge loses its CEE producer identity")
                if candidate.get("produced_during") != execution.get("id"):
                    errors.append("ICLA-3: candidate knowledge loses its execution identity")
                if candidate.get("institutional_authority") != "candidate-pending-adjudication":
                    errors.append(
                        "ICLA-8: CEE-produced knowledge claims authority before adjudication"
                    )

        if resolution and assembly:
            admitted = {
                (item.get("capability"), item.get("ckc"), item.get("version"))
                for item in resolution.get("admission", {}).get("admitted_capabilities", [])
            }
            assembled = {
                (item.get("capability"), item.get("ckc"), item.get("version"))
                for item in assembly.get("ckc_snapshot", [])
            }
            if admitted != assembled:
                errors.append("ICLA-5/6: assembly CKC snapshot differs from admitted resolution")
            if assembly.get("lineage", {}).get("resolution_ref") != resolution.get("id"):
                errors.append("ICLA-5: assembly does not reference the resolved intent result")

        if (
            assembly
            and evidence
            and evidence.get("lineage", {}).get("assembly_ref") != assembly.get("id")
        ):
            errors.append("ICLA-8: evidence does not reference the retained assembly")

        if assembly and evidence:
            selected_roles = {
                role
                for role, items in assembly.get("selection", {})
                .get("knowledge_role_composition", {})
                .items()
                if items
            }
            consumed_roles = set(evidence.get("execution", {}).get("consumed_memory_roles", []))
            if selected_roles != consumed_roles:
                errors.append(
                    "ICLA-6: CEE-consumed memory roles differ from the authorized assembly"
                )

        if evidence and decision:
            receipt = evidence.get("gateway_receipt", {})
            inputs = decision.get("inputs", {})
            if inputs.get("evidence_ref") != evidence.get("id"):
                errors.append("ICLA-9: decision does not reference the evidence bundle")
            if inputs.get("qualification_receipt_ref") != receipt.get("id"):
                errors.append("ICLA-9: decision does not reference the gateway receipt")
            candidates = {
                candidate.get("id"): candidate
                for candidate in evidence.get("candidate_knowledge", [])
                if candidate.get("id")
            }
            for disposition in decision.get("dispositions", {}).values():
                if not isinstance(disposition, dict) or not disposition.get("candidate_ref"):
                    continue
                candidate = candidates.get(disposition["candidate_ref"])
                if candidate is None:
                    errors.append("ICLA-9: adjudication references unknown candidate knowledge")
                    continue
                if disposition.get("memory_transition") != candidate.get("proposed_transition"):
                    errors.append(
                        "ICLA-9: adjudicated memory transition differs from the evidence proposal"
                    )

        if decision:
            activation = decision.get("activation", {})
            matching_successor = any(
                artifact.get("document_type") == "capability-knowledge-contract"
                and artifact.get("id") == activation.get("ckc")
                and artifact.get("version") == activation.get("version")
                and artifact.get("capability_ref") == activation.get("capability")
                for artifact in values
            )
            if activation and not matching_successor:
                errors.append("ICLA-9: activation has no matching successor CKC artifact")
            successor = next(
                (
                    artifact
                    for artifact in values
                    if artifact.get("document_type") == "capability-knowledge-contract"
                    and artifact.get("id") == activation.get("ckc")
                    and artifact.get("version") == activation.get("version")
                ),
                None,
            )
            admitted_transition = decision.get("dispositions", {}).get(
                "reusable_compatibility_pattern", {}
            ).get("memory_transition")
            successor_transition = (
                successor.get("governance", {}).get("memory_role_delta") if successor else None
            )
            if admitted_transition and successor_transition:
                comparable_successor = {
                    key: successor_transition.get(key) for key in ("from", "to")
                }
                comparable_decision = {
                    key: admitted_transition.get(key) for key in ("from", "to")
                }
                if comparable_successor != comparable_decision:
                    errors.append(
                        "ICLA-9: successor CKC memory-role delta differs from adjudication"
                    )
        return errors

    def require_trace(
        self,
        artifacts: Iterable[dict[str, Any]],
        profile: ConformanceProfile = ConformanceProfile.CORE,
    ) -> None:
        errors = self.check_trace(artifacts, profile)
        if errors:
            raise ConformanceError("\n".join(errors))

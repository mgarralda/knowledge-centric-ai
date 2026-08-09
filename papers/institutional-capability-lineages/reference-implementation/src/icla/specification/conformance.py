"""
Institutional Capability Lineage Architecture (ICLA)
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
            errors.append(f"ICLA-2: metric {metric.get('id', '<unknown>')} misses {metric_missing}")
    if artifact.get("governance", {}).get("immutable") is not True:
        errors.append("ICLA-2: CKC version is not declared immutable")
    return errors


def check_icla_3_distributed_authority(artifact: dict[str, Any]) -> list[str]:
    """CEE boundaries are situated; their outputs gain authority only by adjudication."""
    document_type = artifact.get("document_type")
    if document_type == "operational-intent":
        cee = artifact.get("cee", {})
        errors = []
        if cee.get("boundary_scope") != "execution-scoped":
            errors.append("ICLA-3: intent lacks an execution-scoped CEE boundary")
        configuration = cee.get("configuration", {})
        missing = _missing(
            configuration,
            (
                "id",
                "resolution",
                "authorization",
                "assurance",
                "traceability",
                "evidence_interpretation",
            ),
        )
        if missing:
            errors.append(f"ICLA-3: CEE boundary configuration misses {missing}")
        return errors
    if document_type == "capability-knowledge-contract":
        errors = []
        if not artifact.get("source_bindings"):
            errors.append("ICLA-3: CKC has no identified source bindings")
        if not artifact.get("authorities") or not artifact.get("governance"):
            errors.append("ICLA-3: CKC has no governed authority declaration")
        return errors
    if document_type == "contextual-assembly":
        errors = []
        mandate = artifact.get("operational_mandate", {})
        if mandate.get("authority_scope") != "execution-scoped":
            errors.append("ICLA-3: assembly lacks an execution-scoped operational mandate")
        if mandate.get("institutional_change_authority") is not False:
            errors.append("ICLA-3: operational mandate grants institutional change authority")
        if mandate.get("evidence_disclosure") != "evidence-contract-only":
            errors.append("ICLA-3: mandate requires disclosure beyond the evidence contract")
        if mandate.get("registry_interaction") != "reresolution-or-evidence-only":
            errors.append("ICLA-3: mandate implies step-wise Registry control of CEE execution")
        evidence_contract = artifact.get("evidence_contract", {})
        if evidence_contract.get("selection_mode") != "contract-selected":
            errors.append("ICLA-3: assembly does not contractually select submitted evidence")
        return errors
    if document_type == "execution-evidence-bundle":
        errors = []
        execution = artifact.get("execution", {})
        if _missing(execution, ("id", "cee_ref", "cee_configuration_ref", "consumer")):
            errors.append(
                "ICLA-3: evidence has no originating execution, CEE boundary configuration, "
                "or consumer"
            )
        if _missing(artifact.get("lineage", {}), ("assembly_ref", "source_versions")):
            errors.append("ICLA-3: evidence has no identified governed submission path")
        if artifact.get("canonical_mutation") is True:
            errors.append("ICLA-3: a CEE contribution cannot directly mutate canonical state")
        local_execution = execution.get("local_execution", {})
        if local_execution.get("registry_stepwise_interaction") is not False:
            errors.append("ICLA-3: conformance cannot require step-wise CEE interaction")
        if local_execution.get("wholesale_working_state_capture") is not False:
            errors.append("ICLA-3: evidence requires wholesale CEE working-state capture")
        if execution.get("submission", {}).get("selection_mode") != "contract-selected":
            errors.append("ICLA-3: evidence is not contract-selected")
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
        required = ("id", "domain", "lifecycle", "owner", "policy_refs", "conditions")
        missing = _missing(item, required)
        if item.get("lifecycle") == "active":
            missing.extend(_missing(item, ("active_ckc",)))
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
    history = registry.get("pre_resolution_history")
    if not history:
        return errors

    change = history.get("change_event", {})
    impact = history.get("impact_record", {})
    decision = history.get("governance_decision", {})
    delta = history.get("successor_delta", {})
    successor_append = history.get("successor_append", {})
    activation = history.get("activation", {})
    historical = history.get("historical_immutability", {})
    if impact.get("change_event_ref") != change.get("id"):
        errors.append("ICLA-4/9: pre-resolution impact is not linked to its change event")
    if decision.get("change_event_ref") != change.get("id") or decision.get(
        "impact_record_ref"
    ) != impact.get("id"):
        errors.append("ICLA-4/9: pre-resolution governance is not linked to change and impact")
    if any(item not in capability_ids for item in impact.get("affected_capabilities", [])):
        errors.append("ICLA-4/9: pre-resolution impact names an unknown capability")
    registry_relations = {
        (item.get("type"), item.get("from"), item.get("to"))
        for item in registry.get("relations", [])
    }
    impact_relations = {
        (item.get("type"), item.get("from"), item.get("to"))
        for item in impact.get("traversed_relations", [])
    }
    if not impact_relations.issubset(registry_relations):
        errors.append("ICLA-4/9: pre-resolution impact traverses an undeclared relation")
    pointer = activation.get("active_pointer_transition", {})
    capability = next(
        (item for item in capabilities if item.get("id") == activation.get("capability")),
        {},
    )
    active_ckc = capability.get("active_ckc", {})
    expected_active_ref = (
        f"{active_ckc.get('id')}-v{active_ckc.get('version')}" if active_ckc else None
    )
    if (
        decision.get("status") != "approved"
        or delta.get("authorization_decision_ref") != decision.get("id")
        or successor_append.get("authorization_decision_ref") != decision.get("id")
        or successor_append.get("delta_ref") != delta.get("id")
        or successor_append.get("predecessor_ref") != delta.get("predecessor_ref")
        or successor_append.get("successor_ref") != delta.get("successor_ref")
        or successor_append.get("status") != "inactive-successor"
        or activation.get("successor_append_ref") != successor_append.get("id")
        or delta.get("predecessor_ref") != pointer.get("from")
        or delta.get("successor_ref") != pointer.get("to")
        or pointer.get("to") != expected_active_ref
        or active_ckc.get("activation_record") != activation.get("id")
    ):
        errors.append("ICLA-4/9: pre-resolution successor activation is internally inconsistent")
    if historical.get("retroactive_mutation") is not False or any(
        item.get("remains_linked_to") != pointer.get("from")
        for item in historical.get("retained_assemblies", [])
    ):
        errors.append(
            "ICLA-4/9: pre-resolution activation does not preserve predecessor assemblies"
        )
    return errors


def check_icla_5_intent_traceability(artifact: dict[str, Any]) -> list[str]:
    document_type = artifact.get("document_type")
    if document_type == "capability-resolution":
        errors = []
        missing = _missing(
            artifact,
            (
                "cee_ref",
                "cee_configuration_ref",
                "intent_ref",
                "registry_snapshot_ref",
                "admission",
            ),
        )
        if missing:
            errors.append(f"ICLA-5: resolution misses trace fields {missing}")
        matcher = artifact.get("matcher", {})
        confidence = artifact.get("confidence", {})
        if _missing(matcher, ("id", "version", "method")) or _missing(
            confidence, ("mode", "calibration")
        ):
            errors.append(
                "ICLA-5: resolution lacks matcher identity/version or confidence semantics"
            )
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
            (
                "cee_ref",
                "cee_configuration_ref",
                "intent_ref",
                "registry_snapshot_ref",
                "resolution_ref",
                "admission_ref",
            ),
        )
        if missing:
            errors.append(f"ICLA-5: assembly misses execution trace fields {missing}")
        correctness = artifact.get("correctness", {})
        required = ("traceable", "authorized", "required_covered", "mandate_bounded")
        failed = [name for name in required if correctness.get(name) is not True]
        if failed:
            errors.append(f"ICLA-5: authoritative assembly fails {failed}")
        coverage_assessment = artifact.get("correctness_trace", {}).get(
            "required_covered", {}
        )
        coverage_reference = coverage_assessment.get("applicable_reference", {})
        if _missing(coverage_assessment, ("applied_method", "applicable_reference")) or _missing(
            coverage_reference, ("kind", "id", "version")
        ):
            errors.append(
                "ICLA-5: RequiredCovered trace lacks its applied method or versioned reference"
            )
        conflict_trace = artifact.get("correctness_trace", {}).get(
            "conflicts_resolved", {}
        )
        applicable_conflicts = conflict_trace.get("applicable_conflicts")
        if not isinstance(applicable_conflicts, list):
            errors.append("ICLA-5: ConflictsResolved trace is missing")
        elif any(
            _missing(item, ("conflict_ref", "resolution_outcome", "policy_basis"))
            or item.get("assembly_compatible") is not True
            or _missing(item.get("policy_basis", {}), ("id", "version"))
            for item in applicable_conflicts
        ):
            errors.append(
                "ICLA-5: ConflictsResolved trace lacks an outcome or versioned policy basis"
            )
        return errors
    return []


def check_icla_6_assembly_lineage(artifact: dict[str, Any]) -> list[str]:
    if artifact.get("document_type") != "contextual-assembly":
        return []
    errors = []
    lineage_missing = _missing(
        artifact.get("lineage", {}),
        (
            "cee_ref",
            "cee_configuration_ref",
            "intent_ref",
            "registry_snapshot_ref",
            "resolution_ref",
            "admission_ref",
        ),
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
    for transformation in artifact.get("lineage", {}).get(
        "submitted_report_transformations", []
    ):
        if _missing(transformation, ("id", "version")):
            errors.append(
                "ICLA-8: submitted-report transformation is not version-referenced"
            )
    if artifact.get("status") in {"qualified-for-review", "adjudicated"} and not artifact.get(
        "gateway_receipt"
    ):
        errors.append("ICLA-8: qualified evidence has no gateway receipt")
    return errors


def check_icla_9_governed_activation(artifact: dict[str, Any]) -> list[str]:
    if artifact.get("document_type") != "governance-decision":
        return []
    if artifact.get("capability_formation", {}).get(
        "new_capability_created_by_this_decision"
    ) is True:
        return []
    activation = artifact.get("activation", {})
    delta = artifact.get("successor_delta", {})
    successor_append = artifact.get("successor_append", {})
    if not activation and not delta and not successor_append:
        return []
    errors = []
    if artifact.get("status") != "approved":
        errors.append("ICLA-9: succession and activation require approved decisions")
    if _missing(
        artifact.get("impact_record", {}),
        ("id", "affected_capabilities", "affected_ckcs"),
    ):
        errors.append("ICLA-9: canonical change has no impact record")
    if delta:
        if _missing(
            delta,
            (
                "id",
                "predecessor_ref",
                "successor_ref",
                "changed_commitments",
                "rationale",
                "supporting_evidence_refs",
                "authorization_decision_ref",
                "rollback_ref",
            ),
        ):
            errors.append(
                "ICLA-9: canonical change has no complete decision-linked successor delta"
            )
        elif (
            delta.get("authorization_decision_ref") != artifact.get("id")
            or delta.get("rollback_ref") != delta.get("predecessor_ref")
            or delta.get("successor_complete") is not True
            or delta.get("reconstruction_patch") is not False
        ):
            errors.append(
                "ICLA-9: successor delta is not an authorized complete-contract change record"
            )
        required_evidence_refs = {
            artifact.get("inputs", {}).get("evidence_ref"),
            artifact.get("inputs", {}).get("qualification_receipt_ref"),
        } - {None, ""}
        if not required_evidence_refs.issubset(set(delta.get("supporting_evidence_refs", []))):
            errors.append("ICLA-9: successor delta omits its supporting evidence or receipt")
        if not successor_append:
            errors.append("ICLA-9: authorized successor has no distinct append record")

    if successor_append:
        append_missing = _missing(
            successor_append,
            (
                "id",
                "capability",
                "predecessor_ref",
                "successor_ref",
                "delta_ref",
                "authorization_decision_ref",
                "status",
            ),
        )
        if append_missing:
            errors.append(f"ICLA-9: successor append misses {append_missing}")
        elif (
            successor_append.get("authorization_decision_ref") != artifact.get("id")
            or successor_append.get("status") != "inactive-successor"
            or successor_append.get("delta_ref") != delta.get("id")
            or successor_append.get("predecessor_ref") != delta.get("predecessor_ref")
            or successor_append.get("successor_ref") != delta.get("successor_ref")
        ):
            errors.append("ICLA-9: append is not the authorized inactive successor transition")

    if activation:
        if _missing(
            activation,
            (
                "id",
                "capability",
                "ckc",
                "version",
                "successor_append_ref",
                "active_pointer_transition",
                "rollback_target",
            ),
        ):
            errors.append("ICLA-9: activation target is incomplete")
        transition = activation.get("active_pointer_transition")
        if not isinstance(transition, dict) or _missing(transition, ("from", "to")):
            errors.append("ICLA-9: activation does not declare the exact pointer transition")
        elif activation.get("rollback_target") != transition.get("from"):
            errors.append("ICLA-9: activation rollback target is not the exact predecessor")
        if successor_append and activation.get("successor_append_ref") != successor_append.get(
            "id"
        ):
            errors.append("ICLA-9: activation does not reference the appended successor")
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
    if not artifact.get("retention", {}).get("policy_ref") or not artifact.get("access_policy_ref"):
        errors.append("ICLA-10: assembly lacks retention or access policy metadata")
    return errors


def check_icla_11_discovery_authority(artifact: dict[str, Any]) -> list[str]:
    document_type = artifact.get("document_type")
    errors = []
    forbidden_identity_fields = {
        "assigned_identity",
        "institutional_capability_id",
        "capability_ref",
    }
    if document_type == "institutional-capability":
        if artifact.get("lifecycle") in {"candidate", "submitted"}:
            errors.append(
                "ICLA-11: an institutional capability cannot use a pre-institutional lifecycle"
            )
        return errors
    if document_type == "institutional-capability-registry-snapshot":
        if any(
            item.get("lifecycle") in {"candidate", "submitted"}
            for item in artifact.get("capabilities", [])
        ):
            errors.append(
                "ICLA-11: Registry capability uses a pre-institutional lifecycle"
            )
        return errors
    if document_type == "capability-proposal":
        status = artifact.get("status")
        if status not in {"candidate", "submitted"}:
            errors.append("ICLA-11: pre-institutional proposal must be candidate or submitted")
        if forbidden_identity_fields & artifact.keys():
            errors.append("ICLA-11: proposal carries institutional identity before promotion")
        draft_ref = artifact.get("proposal_scoped_ckc_draft_ref")
        if isinstance(draft_ref, str) and draft_ref.startswith("CKC-"):
            errors.append("ICLA-11: proposal draft anticipates an institutional CKC identity")
        recurrence = artifact.get("recurrence_assessment", {})
        if status == "submitted" and recurrence.get("established") is not True:
            errors.append("ICLA-11: submitted proposal does not establish recurrence")
        return errors
    if document_type != "governance-decision":
        return []

    formation = artifact.get("capability_formation", {})
    if formation.get("new_capability_created_by_this_decision") is not True:
        return errors
    promotion = formation.get("governed_promotion", {})
    if not promotion.get("proposal_ref"):
        errors.append("ICLA-11: promotion must reference a submitted proposal")
    review = artifact.get("review", {})
    if (
        artifact.get("status") != "approved"
        or not review.get("authority")
        or promotion.get("review_decision_ref") != artifact.get("id")
    ):
        errors.append("ICLA-11: promotion must reference an authorized review decision")
    assigned = promotion.get("assigned_capability", {})
    append = formation.get("formation_append", {})
    if _missing(assigned, ("id", "name", "outcome", "owner", "domain", "lifecycle")):
        errors.append("ICLA-11: promotion does not define the assigned capability identity")
    if assigned.get("lifecycle") != "approved" or assigned.get("active_ckc"):
        errors.append("ICLA-11: promotion must form an approved capability without activation")
    if (
        _missing(
            append,
            (
                "id",
                "proposal_ref",
                "capability_ref",
                "initial_ckc_ref",
                "authorization_decision_ref",
                "status",
            ),
        )
        or append.get("proposal_ref") != promotion.get("proposal_ref")
        or append.get("capability_ref") != assigned.get("id")
        or append.get("initial_ckc_ref") != promotion.get("initial_ckc_ref")
        or append.get("authorization_decision_ref") != artifact.get("id")
        or append.get("status") != "inactive-initial-ckc"
    ):
        errors.append("ICLA-11: promotion lacks its exact identity-and-initial-CKC append")
    activation = artifact.get("activation", {})
    if activation:
        transition = activation.get("active_pointer_transition", {})
        if (
            not activation.get("id")
            or activation.get("activation_kind") != "initial"
            or activation.get("formation_append_ref") != append.get("id")
            or transition.get("from") is not None
            or activation.get("rollback_target") is not None
        ):
            errors.append(
                "ICLA-11: initial activation is not separately identifiable from promotion"
            )
    return errors


def check_icla_evolving_controls(artifact: dict[str, Any]) -> list[str]:
    """Additional observable capabilities required by the ICLA-Evolving profile."""
    document_type = artifact.get("document_type")
    if document_type == "execution-evidence-bundle":
        return [
            "ICLA-Evolving: candidate knowledge has no explicit lifecycle state"
            for candidate in artifact.get("candidate_knowledge", [])
            if candidate.get("lifecycle_status") != "submitted"
        ]
    if document_type == "capability-proposal":
        required = (
            "id",
            "status",
            "proposed_responsibility",
            "pattern_signal_refs",
            "recurrence_assessment",
            "stable_assembly_rules",
            "value_assessment",
            "comparable_outcome_refs",
            "candidate_owner",
            "overlap_analysis",
            "proposal_scoped_ckc_draft_ref",
        )
        missing = _missing(artifact, required)
        return [f"ICLA-Evolving: crystallization proposal misses {missing}"] if missing else []
    if document_type != "governance-decision":
        return []

    errors = []
    if artifact.get("capability_formation", {}).get(
        "new_capability_created_by_this_decision"
    ) is True:
        review = artifact.get("review", {})
        for field in (
            "ownership_review",
            "distinctiveness_review",
            "overlap_review",
            "value_review",
            "evidence_review",
        ):
            if not _passed(review.get(field)):
                errors.append(f"ICLA-Evolving: capability formation lacks {field}")
        if not artifact.get("inputs", {}).get("supporting_history_refs"):
            errors.append("ICLA-Evolving: capability formation lacks recurrent history")
        return errors
    impact = artifact.get("impact_record", {})
    if impact.get("assessment_mode") != "continuous-event-driven" or not impact.get(
        "change_event_ref"
    ):
        errors.append(
            "ICLA-Evolving: impact analysis is not linked to an identified continuous event"
        )
    activation = artifact.get("activation", {})
    transition = activation.get("active_pointer_transition", {})
    if activation and (
        not activation.get("rollback_target")
        or activation.get("rollback_target") != transition.get("from")
    ):
        errors.append("ICLA-Evolving: activation has no exact rollback target")
    for disposition in artifact.get("dispositions", {}).values():
        if not isinstance(disposition, dict) or not disposition.get("candidate_ref"):
            continue
        lifecycle = disposition.get("candidate_lifecycle_transition", {})
        if lifecycle.get("from") != "submitted" or lifecycle.get("to") not in {
            "admitted",
            "rejected",
            "quarantined",
            "retained-local",
        }:
            errors.append("ICLA-Evolving: candidate disposition has no governed lifecycle")

    return errors


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
    _evolving = _governed + (
        check_icla_11_discovery_authority,
        check_icla_evolving_controls,
    )

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
        proposal_ids = [
            artifact.get("id")
            for artifact in values
            if artifact.get("document_type") == "capability-proposal"
        ]
        if len(proposal_ids) != len(set(proposal_ids)):
            errors.append("ICLA-11: crystallization proposal identifiers must be unique")
        proposal_id_set = set(proposal_ids)
        for artifact in values:
            if artifact.get("document_type") != "governance-decision":
                continue
            referenced = set(artifact.get("capability_formation", {}).get("proposal_refs", []))
            if not referenced.issubset(proposal_id_set):
                errors.append("ICLA-11: governance decision references an unknown proposal")
        by_type = {artifact.get("document_type"): artifact for artifact in values}
        intent = by_type.get("operational-intent", {})
        resolution = by_type.get("capability-resolution", {})
        assembly = by_type.get("contextual-assembly", {})
        evidence = by_type.get("execution-evidence-bundle", {})
        decision = by_type.get("governance-decision", {})

        if intent:
            cee_id = intent.get("cee", {}).get("id")
            cee_configuration_id = intent.get("cee", {}).get("configuration", {}).get("id")
            downstream_cee_refs = {
                resolution.get("cee_ref"),
                assembly.get("lineage", {}).get("cee_ref"),
                evidence.get("execution", {}).get("cee_ref"),
            }
            if downstream_cee_refs - {None, cee_id}:
                errors.append("ICLA-5: situated CEE boundary changes across the execution trace")
            downstream_configuration_refs = {
                resolution.get("cee_configuration_ref"),
                assembly.get("lineage", {}).get("cee_configuration_ref"),
                evidence.get("execution", {}).get("cee_configuration_ref"),
            }
            if downstream_configuration_refs - {None, cee_configuration_id}:
                errors.append("ICLA-3/5: CEE configuration changes across the execution trace")

        if evidence:
            execution = evidence.get("execution", {})
            candidates = evidence.get("candidate_knowledge", [])
            if (
                candidates
                and execution.get("produced_knowledge", {}).get("institutional_authority")
                is not False
            ):
                errors.append("ICLA-3/8: CEE-produced knowledge must remain non-authoritative")
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
            execution = evidence.get("execution", {})
            if execution.get("mandate_ref") != assembly.get("id"):
                errors.append("ICLA-5: execution does not reference its operational mandate")
            materialization_ids = {
                item.get("id") for item in assembly.get("materializations", []) if item.get("id")
            }
            if execution.get("materialization_ref") not in materialization_ids:
                errors.append("ICLA-6: execution uses an unrecorded materialization")
            if execution.get("submission", {}).get("selection_mode") != assembly.get(
                "evidence_contract", {}
            ).get("selection_mode"):
                errors.append("ICLA-8: evidence submission exceeds the assembly contract")
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
                lifecycle = disposition.get("candidate_lifecycle_transition", {})
                if lifecycle.get("from") != candidate.get("lifecycle_status"):
                    errors.append("ICLA-Evolving: candidate lifecycle loses its submitted state")

        if decision and decision.get("capability_formation", {}).get(
            "new_capability_created_by_this_decision"
        ) is not True:
            activation = decision.get("activation", {})
            successor_append = decision.get("successor_append", {})
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
            admitted_transition = (
                decision.get("dispositions", {})
                .get("reusable_compatibility_pattern", {})
                .get("memory_transition")
            )
            successor_transition = (
                successor.get("governance", {}).get("memory_role_delta") if successor else None
            )
            if successor:
                authorizing_decision = successor.get("generated_from", {}).get(
                    "governance_decision"
                ) or successor.get("governance", {}).get("admission_decision_ref")
                expected_construction_decision = successor_append.get(
                    "authorization_decision_ref"
                ) or decision.get("id")
                if authorizing_decision != expected_construction_decision:
                    errors.append("ICLA-9: successor CKC is not linked to its authorizing decision")
                predecessor_refs = {
                    successor.get("predecessor"),
                    successor.get("generated_from", {}).get("predecessor"),
                }
                declared_predecessor = successor_append.get("predecessor_ref") or activation.get(
                    "active_pointer_transition", {}
                ).get("from")
                if declared_predecessor not in predecessor_refs:
                    errors.append(
                        "ICLA-9: successor CKC predecessor differs from the approved transition"
                    )
                delta = decision.get("successor_delta", {})
                successor_delta_refs = {
                    successor.get("generated_from", {}).get("successor_delta"),
                    successor.get("governance", {}).get("successor_delta_ref"),
                }
                if delta and successor_delta_refs != {delta.get("id")}:
                    errors.append(
                        "ICLA-9: complete successor CKC is not linked to the decision "
                        "successor delta"
                    )
                if successor_append and (
                    successor_append.get("successor_ref")
                    not in {
                        f"{successor.get('id')}@{successor.get('version')}",
                        f"{successor.get('id')}-v{successor.get('version')}",
                    }
                    or activation.get("successor_append_ref") != successor_append.get("id")
                ):
                    errors.append(
                        "ICLA-9: activation is not linked through the exact successor append"
                    )
            if admitted_transition and successor_transition:
                comparable_successor = {
                    key: successor_transition.get(key) for key in ("from", "to")
                }
                comparable_decision = {key: admitted_transition.get(key) for key in ("from", "to")}
                if comparable_successor != comparable_decision:
                    errors.append(
                        "ICLA-9: successor CKC memory-role delta differs from adjudication"
                    )
        errors.extend(self._check_formation_trace(values))
        return errors

    @staticmethod
    def _check_formation_trace(values: list[dict[str, Any]]) -> list[str]:
        """Check the observable Eq. (14)/(17) formation path across retained artifacts."""
        decisions = [
            item
            for item in values
            if item.get("document_type") == "governance-decision"
            and item.get("capability_formation", {}).get(
                "new_capability_created_by_this_decision"
            )
            is True
        ]
        if not decisions:
            return []
        if len(decisions) != 1:
            return ["ICLA-11: reference formation trace must contain one promotion decision"]

        errors: list[str] = []
        decision = decisions[0]
        formation = decision.get("capability_formation", {})
        promotion = formation.get("governed_promotion", {})
        append = formation.get("formation_append", {})
        activation = decision.get("activation", {})
        proposal_ref = promotion.get("proposal_ref")
        proposal = next(
            (
                item
                for item in values
                if item.get("document_type") == "capability-proposal"
                and item.get("id") == proposal_ref
            ),
            None,
        )
        if proposal is None or proposal.get("status") != "submitted":
            errors.append("ICLA-11: promotion has no matching submitted proposal artifact")
            return errors

        assigned = promotion.get("assigned_capability", {})
        capability_id = assigned.get("id")
        initial_ckc = next(
            (
                item
                for item in values
                if item.get("document_type") == "capability-knowledge-contract"
                and item.get("capability_ref") == capability_id
                and item.get("version") == 1
            ),
            None,
        )
        if initial_ckc is None:
            errors.append("ICLA-11: promotion has no matching initial CKC v1 artifact")
        else:
            initial_refs = {
                f"{initial_ckc.get('id')}@1",
                f"{initial_ckc.get('id')}-v1",
            }
            provenance = initial_ckc.get("generated_from", {})
            history = set(proposal.get("pattern_signal_refs", []))
            if (
                promotion.get("initial_ckc_ref") not in initial_refs
                or append.get("initial_ckc_ref") not in initial_refs
                or provenance.get("capability_proposal") != proposal_ref
                or provenance.get("governance_decision") != decision.get("id")
                or provenance.get("formation_append") != append.get("id")
                or not history.issubset(set(provenance.get("recurrent_history", [])))
            ):
                errors.append(
                    "ICLA-11: initial CKC loses its proposal, decision, or history origin"
                )

        registries = {
            item.get("id"): item
            for item in values
            if item.get("document_type") == "institutional-capability-registry-snapshot"
        }
        before = registries.get(decision.get("inputs", {}).get("registry_snapshot_ref"))
        formed = registries.get(formation.get("formed_registry_snapshot_ref"))
        active = registries.get(activation.get("resulting_registry_snapshot_ref"))
        if not before or not formed or not active:
            errors.append("ICLA-11: formation trace lacks before, formed, or active Registry state")
            return errors

        def capability(snapshot: dict[str, Any]) -> dict[str, Any] | None:
            return next(
                (
                    item
                    for item in snapshot.get("capabilities", [])
                    if item.get("id") == capability_id
                ),
                None,
            )

        before_capability = capability(before)
        formed_capability = capability(formed)
        active_capability = capability(active)
        if before_capability is not None:
            errors.append("ICLA-11: assigned identity exists before governed promotion")
        if (
            formed_capability is None
            or formed_capability.get("lifecycle") != "approved"
            or formed_capability.get("active_ckc")
        ):
            errors.append("ICLA-11: promotion does not preserve a formed, inactive state")
        expected_active = {
            "id": initial_ckc.get("id") if initial_ckc else None,
            "version": 1,
        }
        if (
            active_capability is None
            or active_capability.get("lifecycle") != "active"
            or active_capability.get("active_ckc") != expected_active
        ):
            errors.append("ICLA-11: separate activation does not publish the initial CKC v1")

        before_by_id = {item.get("id"): item for item in before.get("capabilities", [])}
        formed_by_id = {item.get("id"): item for item in formed.get("capabilities", [])}
        active_by_id = {item.get("id"): item for item in active.get("capabilities", [])}
        if any(formed_by_id.get(key) != value for key, value in before_by_id.items()):
            errors.append("ICLA-11: promotion rewrites pre-existing Registry capabilities")
        if any(active_by_id.get(key) != value for key, value in before_by_id.items()):
            errors.append("ICLA-11: initial activation rewrites pre-existing capabilities")

        history = set(proposal.get("pattern_signal_refs", []))
        if not history.issubset(set(decision.get("inputs", {}).get("supporting_history_refs", []))):
            errors.append("ICLA-11: review omits recurrent proposal history")
        if not history.issubset(
            set(decision.get("historical_immutability", {}).get("retained_history_refs", []))
        ):
            errors.append("ICLA-11: promotion does not preserve its recurrent history")

        edges = {
            (item.get("from"), item.get("type"), item.get("to"))
            for item in decision.get("resulting_lineage_edges", [])
        }
        required_edges = {
            (append.get("id"), "authorized_by", decision.get("id")),
            (append.get("id"), "forms", capability_id),
            (capability_id, "derived_from", proposal_ref),
            (activation.get("id"), "activates", f"{initial_ckc.get('id')}@1")
            if initial_ckc
            else (None, None, None),
        }
        if not required_edges.issubset(edges):
            errors.append("ICLA-11: capability formation lineage is incomplete")
        return errors

    def require_trace(
        self,
        artifacts: Iterable[dict[str, Any]],
        profile: ConformanceProfile = ConformanceProfile.CORE,
    ) -> None:
        errors = self.check_trace(artifacts, profile)
        if errors:
            raise ConformanceError("\n".join(errors))

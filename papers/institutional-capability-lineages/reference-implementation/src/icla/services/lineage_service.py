"""
Institutional Capability Lineage Architecture (ICLA)
Reference Implementation

Copyright (c) 2026 Mariano Garralda-Barrio

Licensed under the MIT License.
See the LICENSE file in the repository root for details.
"""

from typing import Any

from ..models.lineage import InstitutionalCapabilityLineage, LineageEdge, LineageNode
from ..repositories.lineage_repository import LineageRepository


class LineageService:
    def __init__(self, repository: LineageRepository | None = None) -> None:
        self.repository = repository

    def build_lineage(
        self, capability_id: str, artifacts: list[dict] | None = None
    ) -> InstitutionalCapabilityLineage:
        if artifacts is None:
            return (
                self.repository.get_capability_lineage(capability_id)
                if self.repository
                else InstitutionalCapabilityLineage(capability_id=capability_id)
            )
        nodes_by_id = {
            self._artifact_node_id(item): LineageNode(
                id=self._artifact_node_id(item),
                node_type=item.get("document_type", "artifact"),
                artifact_ref=self._artifact_node_id(item),
            )
            for item in artifacts
        }
        edges: list[LineageEdge] = []
        for item in artifacts:
            edges.extend(self.edges_from_artifact(item))
        unique_edges = {(edge.source, edge.relation_type, edge.target): edge for edge in edges}
        for edge in unique_edges.values():
            for node_id in (edge.source, edge.target):
                nodes_by_id.setdefault(
                    node_id,
                    LineageNode(
                        id=node_id,
                        node_type=self._infer_node_type(node_id),
                        artifact_ref=node_id,
                    ),
                )
        return InstitutionalCapabilityLineage(
            capability_id=capability_id,
            nodes=list(nodes_by_id.values()),
            edges=list(unique_edges.values()),
        )

    def edges_from_artifact(self, artifact: dict[str, Any]) -> list[LineageEdge]:
        document_type = artifact.get("document_type")
        extractors = {
            "institutional-capability-registry-snapshot": self.edges_from_registry_snapshot,
            "capability-resolution": self.edges_from_resolution,
            "contextual-assembly": self.edges_from_assembly,
            "capability-knowledge-contract": self.edges_from_ckc,
            "execution-evidence-bundle": self.edges_from_evidence,
            "governance-decision": self.edges_from_governance_decision,
        }
        if document_type in extractors:
            return extractors[document_type](artifact)
        if "successor_ref" in artifact and "delta_ref" in artifact:
            return self.edges_from_successor_append(artifact)
        if "decision_ref" in artifact and "active_ckc" in artifact:
            return self.edges_from_activation(artifact)
        return []

    @staticmethod
    def edges_from_ckc(artifact: dict[str, Any]) -> list[LineageEdge]:
        ckc_ref = LineageService._versioned_ref(artifact)
        if not ckc_ref:
            return []
        edges = [
            LineageEdge.model_validate(
                {"from": ckc_ref, "type": "contract_for", "to": artifact["capability_ref"]}
            )
        ]
        predecessor = artifact.get("predecessor")
        if predecessor:
            edges.append(
                LineageEdge.model_validate(
                    {
                        "from": ckc_ref,
                        "type": "supersedes",
                        "to": LineageService._normalize_ckc_ref(str(predecessor)),
                    }
                )
            )
        decision = artifact.get("generated_from", {}).get("governance_decision")
        if decision:
            edges.append(
                LineageEdge.model_validate(
                    {"from": ckc_ref, "type": "authorized_by", "to": str(decision)}
                )
            )
        return edges

    @staticmethod
    def edges_from_registry_snapshot(artifact: dict[str, Any]) -> list[LineageEdge]:
        edges = []
        snapshot_id = artifact["id"]
        for capability in artifact.get("capabilities", []):
            capability_id = capability.get("id")
            if not capability_id:
                continue
            edges.append(
                LineageEdge.model_validate(
                    {"from": snapshot_id, "type": "contains", "to": capability_id}
                )
            )
            active_ckc = capability.get("active_ckc", {})
            ckc_ref = LineageService._versioned_ref(active_ckc)
            if ckc_ref:
                edges.append(
                    LineageEdge.model_validate(
                        {"from": capability_id, "type": "activates", "to": ckc_ref}
                    )
                )
        history = artifact.get("pre_resolution_history", {})
        if not history:
            return edges

        change = history.get("change_event", {})
        impact = history.get("impact_record", {})
        decision = history.get("governance_decision", {})
        delta = history.get("successor_delta", {})
        activation = history.get("activation", {})
        change_id = change.get("id")
        impact_id = impact.get("id")
        decision_id = decision.get("id")
        delta_id = delta.get("id")
        activation_id = activation.get("id")
        if change_id:
            edges.append(
                LineageEdge.model_validate(
                    {"from": snapshot_id, "type": "records_change", "to": change_id}
                )
            )
            if change.get("source_binding_ref"):
                edges.append(
                    LineageEdge.model_validate(
                        {
                            "from": change_id,
                            "type": "changes",
                            "to": change["source_binding_ref"],
                        }
                    )
                )
        if impact_id and change_id:
            edges.append(
                LineageEdge.model_validate(
                    {"from": impact_id, "type": "triggered_by", "to": change_id}
                )
            )
        if impact_id:
            for capability_id in impact.get("affected_capabilities", []):
                edges.append(
                    LineageEdge.model_validate(
                        {"from": impact_id, "type": "affects", "to": capability_id}
                    )
                )
            for ckc_ref in impact.get("affected_ckcs", []):
                edges.append(
                    LineageEdge.model_validate(
                        {
                            "from": impact_id,
                            "type": "affects",
                            "to": LineageService._normalize_ckc_ref(str(ckc_ref)),
                        }
                    )
                )
        if decision_id and impact_id:
            edges.append(
                LineageEdge.model_validate(
                    {"from": decision_id, "type": "adjudicates", "to": impact_id}
                )
            )
        if decision_id and delta_id:
            edges.append(
                LineageEdge.model_validate(
                    {"from": decision_id, "type": "authorizes", "to": delta_id}
                )
            )
        predecessor = LineageService._normalize_ckc_ref(str(delta.get("predecessor_ref", "")))
        successor = LineageService._normalize_ckc_ref(str(delta.get("successor_ref", "")))
        if delta_id and predecessor:
            edges.append(
                LineageEdge.model_validate(
                    {"from": delta_id, "type": "changes_from", "to": predecessor}
                )
            )
        if delta_id and successor:
            edges.append(
                LineageEdge.model_validate({"from": delta_id, "type": "describes", "to": successor})
            )
        if activation_id and decision_id:
            edges.append(
                LineageEdge.model_validate(
                    {"from": activation_id, "type": "authorized_by", "to": decision_id}
                )
            )
        if activation_id and successor:
            edges.append(
                LineageEdge.model_validate(
                    {"from": activation_id, "type": "activates", "to": successor}
                )
            )
        if successor and predecessor:
            edges.append(
                LineageEdge.model_validate(
                    {"from": successor, "type": "supersedes", "to": predecessor}
                )
            )
        for retained in history.get("historical_immutability", {}).get("retained_assemblies", []):
            if retained.get("assembly_ref") and retained.get("remains_linked_to"):
                edges.append(
                    LineageEdge.model_validate(
                        {
                            "from": retained["assembly_ref"],
                            "type": "uses",
                            "to": LineageService._normalize_ckc_ref(retained["remains_linked_to"]),
                        }
                    )
                )
        return edges

    @staticmethod
    def edges_from_resolution(artifact: dict[str, Any]) -> list[LineageEdge]:
        resolution_id = artifact["id"]
        edges = LineageService._reference_edges(
            resolution_id,
            artifact,
            {
                "intent_ref": "derived_from",
                "registry_snapshot_ref": "resolved_against",
            },
        )
        admission = artifact.get("admission", {})
        admission_id = admission.get("id")
        if admission_id:
            edges.append(
                LineageEdge.model_validate(
                    {"from": resolution_id, "type": "produced", "to": admission_id}
                )
            )
            for admitted in admission.get("admitted_capabilities", []):
                capability_id = admitted.get("capability")
                if capability_id:
                    edges.append(
                        LineageEdge.model_validate(
                            {"from": admission_id, "type": "admits", "to": capability_id}
                        )
                    )
                ckc_ref = LineageService._versioned_ref(admitted)
                if ckc_ref:
                    edges.append(
                        LineageEdge.model_validate(
                            {"from": admission_id, "type": "admits", "to": ckc_ref}
                        )
                    )
        return edges

    @staticmethod
    def edges_from_assembly(artifact: dict[str, Any]) -> list[LineageEdge]:
        assembly_id = artifact["id"]
        edges = LineageService._reference_edges(
            assembly_id,
            artifact.get("lineage", {}),
            {
                "intent_ref": "derived_from",
                "registry_snapshot_ref": "uses_snapshot",
                "resolution_ref": "derived_from",
                "admission_ref": "derived_from",
            },
        )
        for ckc in artifact.get("ckc_snapshot", []):
            ckc_ref = LineageService._versioned_ref(ckc)
            if ckc_ref:
                edges.append(
                    LineageEdge.model_validate({"from": assembly_id, "type": "uses", "to": ckc_ref})
                )
        return edges

    @staticmethod
    def edges_from_evidence(artifact: dict[str, Any]) -> list[LineageEdge]:
        evidence_id = artifact["id"]
        edges = LineageService._reference_edges(
            evidence_id,
            artifact.get("lineage", {}),
            {
                "intent_ref": "derived_from",
                "registry_snapshot_ref": "uses_snapshot",
                "resolution_ref": "derived_from",
                "admission_ref": "derived_from",
                "assembly_ref": "derived_from",
            },
        )
        execution_id = artifact.get("execution", {}).get("id")
        if execution_id:
            edges.append(
                LineageEdge.model_validate(
                    {"from": execution_id, "type": "submitted_as", "to": evidence_id}
                )
            )
            cee_ref = artifact.get("execution", {}).get("cee_ref")
            if cee_ref:
                edges.append(
                    LineageEdge.model_validate(
                        {"from": execution_id, "type": "performed_by", "to": cee_ref}
                    )
                )
            cee_configuration_ref = artifact.get("execution", {}).get("cee_configuration_ref")
            if cee_configuration_ref:
                edges.append(
                    LineageEdge.model_validate(
                        {
                            "from": execution_id,
                            "type": "configured_as",
                            "to": cee_configuration_ref,
                        }
                    )
                )
            materialization_ref = artifact.get("execution", {}).get("materialization_ref")
            if materialization_ref:
                edges.append(
                    LineageEdge.model_validate(
                        {
                            "from": execution_id,
                            "type": "consumes",
                            "to": materialization_ref,
                        }
                    )
                )
            mandate_ref = artifact.get("execution", {}).get("mandate_ref")
            if mandate_ref:
                edges.append(
                    LineageEdge.model_validate(
                        {
                            "from": execution_id,
                            "type": "operates_under",
                            "to": mandate_ref,
                        }
                    )
                )
        memory_id = artifact.get("memory_record", {}).get("id")
        if memory_id:
            edges.append(
                LineageEdge.model_validate(
                    {"from": memory_id, "type": "records_episode_from", "to": evidence_id}
                )
            )
            for candidate in artifact.get("candidate_knowledge", []):
                if candidate.get("id"):
                    edges.append(
                        LineageEdge.model_validate(
                            {
                                "from": candidate["id"],
                                "type": "derived_from",
                                "to": memory_id,
                            }
                        )
                    )
                    produced_during = candidate.get("produced_during")
                    if produced_during:
                        edges.append(
                            LineageEdge.model_validate(
                                {
                                    "from": candidate["id"],
                                    "type": "produced_during",
                                    "to": produced_during,
                                }
                            )
                        )
        for ckc in artifact.get("lineage", {}).get("exact_ckc_versions", []):
            ckc_ref = LineageService._versioned_ref(ckc) if isinstance(ckc, dict) else str(ckc)
            if ckc_ref:
                edges.append(
                    LineageEdge.model_validate({"from": evidence_id, "type": "uses", "to": ckc_ref})
                )
        return edges

    @staticmethod
    def edges_from_governance_decision(artifact: dict[str, Any]) -> list[LineageEdge]:
        decision_id = artifact["id"]
        edges = LineageService._reference_edges(
            decision_id,
            artifact.get("inputs", {}),
            {
                "evidence_ref": "adjudicates",
                "qualification_receipt_ref": "adjudicates",
                "assembly_ref": "adjudicates",
                "registry_snapshot_ref": "uses_snapshot",
            },
        )
        edges.extend(
            LineageEdge.model_validate(edge) for edge in artifact.get("resulting_lineage_edges", [])
        )
        delta = artifact.get("successor_delta", {})
        if delta.get("id"):
            edges.append(
                LineageEdge.model_validate(
                    {"from": decision_id, "type": "authorizes", "to": delta["id"]}
                )
            )
            for field, relation in (
                ("predecessor_ref", "changes_from"),
                ("successor_ref", "describes"),
                ("rollback_ref", "rolls_back_to"),
            ):
                if delta.get(field):
                    edges.append(
                        LineageEdge.model_validate(
                            {"from": delta["id"], "type": relation, "to": delta[field]}
                        )
                    )
            for evidence_ref in delta.get("supporting_evidence_refs", []):
                edges.append(
                    LineageEdge.model_validate(
                        {
                            "from": delta["id"],
                            "type": "supported_by",
                            "to": evidence_ref,
                        }
                    )
                )
        successor_append = artifact.get("successor_append", {})
        if successor_append.get("id"):
            edges.extend(LineageService.edges_from_successor_append(successor_append))
        return edges

    @staticmethod
    def edges_from_successor_append(artifact: dict[str, Any]) -> list[LineageEdge]:
        append_id = artifact["id"]
        decision_ref = artifact.get("decision_ref") or artifact.get("authorization_decision_ref")
        container = {
            **artifact,
            "decision_ref": decision_ref,
            "capability_ref": artifact.get("capability_ref") or artifact.get("capability"),
        }
        for field in ("predecessor_ref", "successor_ref"):
            if container.get(field):
                container[field] = LineageService._normalize_ckc_ref(str(container[field]))
        edges = LineageService._reference_edges(
            append_id,
            container,
            {
                "decision_ref": "authorized_by",
                "capability_ref": "appends_for",
                "predecessor_ref": "follows",
                "successor_ref": "appends",
                "delta_ref": "explained_by",
            },
        )
        return edges

    @staticmethod
    def edges_from_activation(artifact: dict[str, Any]) -> list[LineageEdge]:
        activation_id = artifact["id"]
        edges = LineageService._reference_edges(
            activation_id,
            artifact,
            {
                "decision_ref": "authorized_by",
                "capability_ref": "activates_for",
                "successor_append_ref": "activates_append",
            },
        )
        previous = LineageService._versioned_ref(artifact.get("previous_ckc", {}))
        active = LineageService._versioned_ref(artifact.get("active_ckc", {}))
        if active:
            edges.append(
                LineageEdge.model_validate(
                    {"from": activation_id, "type": "activates", "to": active}
                )
            )
        if active and previous:
            edges.append(
                LineageEdge.model_validate({"from": active, "type": "supersedes", "to": previous})
            )
        return edges

    @staticmethod
    def _reference_edges(
        source: str,
        container: dict[str, Any],
        relations: dict[str, str],
    ) -> list[LineageEdge]:
        return [
            LineageEdge.model_validate(
                {"from": source, "type": relation, "to": str(container[field])}
            )
            for field, relation in relations.items()
            if container.get(field)
        ]

    @staticmethod
    def _versioned_ref(value: dict[str, Any]) -> str | None:
        identifier = value.get("ckc") or value.get("id")
        version = value.get("version")
        if not identifier:
            return None
        return f"{identifier}@{version}" if version is not None else str(identifier)

    @staticmethod
    def _normalize_ckc_ref(value: str) -> str:
        marker = "-v"
        if value.startswith("CKC-") and marker in value:
            identifier, version = value.rsplit(marker, 1)
            if version.isdigit():
                return f"{identifier}@{version}"
        return value

    @staticmethod
    def _artifact_node_id(artifact: dict[str, Any]) -> str:
        if artifact.get("document_type") == "capability-knowledge-contract":
            return LineageService._versioned_ref(artifact) or str(artifact["id"])
        return str(artifact["id"])

    @staticmethod
    def _infer_node_type(node_id: str) -> str:
        prefixes = {
            "INT-": "operational-intent",
            "REG-SNAP-": "institutional-capability-registry-snapshot",
            "RES-": "capability-resolution",
            "ADM-": "admission-decision",
            "ASM-": "contextual-assembly",
            "MAT-": "materialization",
            "CEE-CONFIG-": "cee-configuration",
            "CEE-": "capability-execution-environment",
            "EXE-": "execution",
            "EVD-": "execution-evidence-bundle",
            "MEM-": "episodic-memory-record",
            "CAND-": "candidate-knowledge",
            "RCPT-": "evidence-receipt",
            "DEC-": "governance-decision",
            "DELTA-": "successor-delta",
            "APPEND-": "successor-append-receipt",
            "ACT-": "activation-record",
            "CAP-": "institutional-capability",
            "CKC-": "capability-knowledge-contract",
        }
        return next(
            (node_type for prefix, node_type in prefixes.items() if node_id.startswith(prefix)),
            "artifact-reference",
        )

    @staticmethod
    def validate_connected_lineage(lineage: InstitutionalCapabilityLineage) -> None:
        LineageRepository.validate_connected_trace(lineage)

    def trace_from_execution(self, execution_id: str, lineage: InstitutionalCapabilityLineage):
        return self._reachable(execution_id, lineage)

    def trace_from_evidence(self, evidence_id: str, lineage: InstitutionalCapabilityLineage):
        return self._reachable(evidence_id, lineage)

    def trace_from_change(self, change_id: str, lineage: InstitutionalCapabilityLineage):
        """Return the connected institutional path initiated by a governed change event."""
        return self._reachable(change_id, lineage)

    @staticmethod
    def _reachable(start: str, lineage: InstitutionalCapabilityLineage) -> set[str]:
        adjacency: dict[str, set[str]] = {}
        for edge in lineage.edges:
            adjacency.setdefault(edge.source, set()).add(edge.target)
            adjacency.setdefault(edge.target, set()).add(edge.source)
        seen, pending = set(), [start]
        while pending:
            current = pending.pop()
            if current not in seen:
                seen.add(current)
                pending.extend(adjacency.get(current, set()) - seen)
        return seen

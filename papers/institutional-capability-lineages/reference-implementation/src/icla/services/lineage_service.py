"""
Institutional Capability Lineages (ICLA)
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
            "CEE-": "capability-execution-environment",
            "EXE-": "execution",
            "EVD-": "execution-evidence-bundle",
            "MEM-": "episodic-memory-record",
            "CAND-": "candidate-knowledge",
            "RCPT-": "evidence-receipt",
            "DEC-": "governance-decision",
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

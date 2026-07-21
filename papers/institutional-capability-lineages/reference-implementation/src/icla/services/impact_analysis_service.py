"""
Institutional Capability Lineages (ICLA)
Reference Implementation

Copyright (c) 2026 Mariano Garralda-Barrio

Licensed under the MIT License.
See the LICENSE file in the repository root for details.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ImpactAnalysis:
    affected_ckcs: tuple[str, ...]
    affected_capabilities: tuple[str, ...]
    retained_assemblies: tuple[str, ...]
    consumers: tuple[str, ...]
    review_required: bool
    rationale: tuple[str, ...]


class ImpactAnalysisService:
    def analyze(self, change: dict, *, registry, ckcs: list, assemblies: list) -> ImpactAnalysis:
        references = self._change_references(change)
        affected_ckc_ids = {ckc.id for ckc in ckcs if self._ckc_is_affected(ckc, references)}
        affected_capability_ids = {ckc.capability_ref for ckc in ckcs if ckc.id in affected_ckc_ids}
        affected_capability_ids.update(
            reference for reference in references if registry.capability(reference) is not None
        )

        relation_change = change.get("relation")
        if isinstance(relation_change, dict):
            affected_capability_ids.update(
                str(relation_change[field])
                for field in ("from", "to")
                if relation_change.get(field)
            )

        propagation_relations = {
            "depends_on",
            "shares_knowledge",
            "specializes",
            "composes_with",
            "replaces",
        }
        changed = True
        while changed:
            changed = False
            for relation in registry.relations:
                if relation.relation_type not in propagation_relations:
                    continue
                if (
                    relation.source in affected_capability_ids
                    or relation.target in affected_capability_ids
                ):
                    before = len(affected_capability_ids)
                    affected_capability_ids.update((relation.source, relation.target))
                    changed = changed or len(affected_capability_ids) > before

        for capability_id in affected_capability_ids:
            capability = registry.capability(capability_id)
            if capability is not None:
                affected_ckc_ids.add(capability.active_ckc.id)

        affected_ckcs = tuple(sorted(affected_ckc_ids))
        affected_capabilities = tuple(sorted(affected_capability_ids))
        retained = tuple(
            sorted(
                a.id
                for a in assemblies
                if any(
                    item.get("ckc") in affected_ckcs
                    or item.get("capability") in affected_capabilities
                    for item in a.ckc_snapshot
                )
            )
        )
        consumers = tuple(
            sorted(
                {
                    str(a.generated_from.get("consumer"))
                    for a in assemblies
                    if a.id in retained and a.generated_from.get("consumer")
                }
            )
        )
        return ImpactAnalysis(
            affected_ckcs,
            affected_capabilities,
            retained,
            consumers,
            bool(affected_ckcs or affected_capabilities),
            (
                f"change references: {sorted(references)}",
                "impact derived from explicit CKC fields and Registry relations",
            ),
        )

    @staticmethod
    def _change_references(change: dict) -> set[str]:
        reference_fields = {
            "artifact_ref",
            "source_ref",
            "policy_ref",
            "ckc_ref",
            "capability_ref",
            "owner_ref",
            "lifecycle_ref",
        }
        return {
            str(value)
            for field, value in change.items()
            if field in reference_fields and value not in (None, "")
        }

    @classmethod
    def _ckc_is_affected(cls, ckc, references: set[str]) -> bool:
        direct = {ckc.id, ckc.capability_ref, ckc.predecessor}
        if references & {str(value) for value in direct if value}:
            return True
        structured_fields = (
            ckc.source_bindings,
            ckc.governance,
            ckc.projection_rules,
            ckc.evidence_contract,
            ckc.evaluation_contract,
        )
        return any(cls._contains_exact(field, references) for field in structured_fields)

    @classmethod
    def _contains_exact(cls, value, references: set[str]) -> bool:
        if isinstance(value, dict):
            return any(cls._contains_exact(item, references) for item in value.values())
        if isinstance(value, (list, tuple, set)):
            return any(cls._contains_exact(item, references) for item in value)
        return str(value) in references if value is not None else False

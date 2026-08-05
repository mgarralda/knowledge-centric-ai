"""
Institutional Capability Lineage Architecture (ICLA)
Reference Implementation

Copyright (c) 2026 Mariano Garralda-Barrio

Licensed under the MIT License.
See the LICENSE file in the repository root for details.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ImpactAnalysis:
    affected_bindings: tuple[str, ...]
    affected_ckcs: tuple[str, ...]
    affected_capabilities: tuple[str, ...]
    traversed_relations: tuple[dict[str, str], ...]
    retained_assemblies: tuple[str, ...]
    affected_cees: tuple[str, ...]
    consumers: tuple[str, ...]
    review_required: bool
    rationale: tuple[str, ...]


@dataclass(frozen=True)
class ImpactEventResult:
    event_ref: str
    sequence: int
    analysis: ImpactAnalysis


class ImpactAnalysisService:
    def analyze(self, change: dict, *, registry, ckcs: list, assemblies: list) -> ImpactAnalysis:
        references = self._change_references(change)
        affected_bindings = {
            str(binding["id"])
            for binding in getattr(registry, "source_bindings", [])
            if binding.get("id")
            and references
            & {
                str(value)
                for value in (
                    binding.get("id"),
                    binding.get("source"),
                    self._versioned_ref(binding.get("source"), binding.get("version")),
                )
                if value
            }
        }
        affected_contracts = [ckc for ckc in ckcs if self._ckc_is_affected(ckc, references)]
        affected_ckc_ids = {self._ckc_ref(ckc) for ckc in affected_contracts}
        affected_capability_ids = {ckc.capability_ref for ckc in affected_contracts}
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
        traversed_relations: dict[tuple[str, str, str], dict[str, str]] = {}
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
                    key = (relation.relation_type, relation.source, relation.target)
                    traversed_relations[key] = {
                        "type": relation.relation_type,
                        "from": relation.source,
                        "to": relation.target,
                    }
                    before = len(affected_capability_ids)
                    affected_capability_ids.update((relation.source, relation.target))
                    changed = changed or len(affected_capability_ids) > before

        for capability_id in affected_capability_ids:
            capability = registry.capability(capability_id)
            if capability is not None:
                affected_ckc_ids.add(
                    self._versioned_ref(capability.active_ckc.id, capability.active_ckc.version)
                )

        affected_ckcs = tuple(sorted(affected_ckc_ids))
        affected_capabilities = tuple(sorted(affected_capability_ids))
        retained = tuple(
            sorted(
                a.id
                for a in assemblies
                if any(
                    self._versioned_ref(item.get("ckc"), item.get("version")) in affected_ckcs
                    for item in a.ckc_snapshot
                )
            )
        )
        affected_cees = tuple(
            sorted(
                {
                    str(a.lineage.get("cee_ref"))
                    for a in assemblies
                    if a.id in retained and a.lineage.get("cee_ref")
                }
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
            tuple(sorted(affected_bindings)),
            affected_ckcs,
            affected_capabilities,
            tuple(traversed_relations[key] for key in sorted(traversed_relations)),
            retained,
            affected_cees,
            consumers,
            bool(affected_bindings or affected_ckcs or affected_capabilities),
            (
                f"change references: {sorted(references)}",
                "impact derived from exact source bindings, CKC versions, and Registry relations",
            ),
        )

    def analyze_change_stream(
        self, changes: list[dict], *, registry, ckcs: list, assemblies: list
    ) -> tuple[ImpactEventResult, ...]:
        """Evaluate an ordered stream of governed change events without mutating prior results."""
        results = []
        for sequence, change in enumerate(changes, start=1):
            event_ref = change.get("id") or change.get("event_ref")
            if not event_ref:
                raise ValueError("Continuous impact analysis requires an identified change event")
            results.append(
                ImpactEventResult(
                    event_ref=str(event_ref),
                    sequence=sequence,
                    analysis=self.analyze(
                        change,
                        registry=registry,
                        ckcs=ckcs,
                        assemblies=assemblies,
                    ),
                )
            )
        return tuple(results)

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
        direct = {ckc.id, cls._ckc_ref(ckc), ckc.capability_ref, ckc.predecessor}
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
    def _ckc_ref(cls, ckc) -> str:
        return cls._versioned_ref(ckc.id, ckc.version)

    @staticmethod
    def _versioned_ref(identifier, version) -> str:
        if identifier in (None, ""):
            return ""
        if version in (None, ""):
            return str(identifier)
        return f"{identifier}-v{version}"

    @classmethod
    def _contains_exact(cls, value, references: set[str]) -> bool:
        if isinstance(value, dict):
            return any(cls._contains_exact(item, references) for item in value.values())
        if isinstance(value, (list, tuple, set)):
            return any(cls._contains_exact(item, references) for item in value)
        return str(value) in references if value is not None else False

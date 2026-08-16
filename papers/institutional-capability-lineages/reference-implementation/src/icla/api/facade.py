"""
Institutional Capability Lineage Architecture (ICLA)
Reference Implementation

Copyright (c) 2026 Mariano Garralda-Barrio

Licensed under the MIT License.
See the LICENSE file in the repository root for details.
"""

# Module purpose: Single public surface; transports should delegate here.

from __future__ import annotations

from pathlib import Path

from ..config import Settings
from ..models import EvidenceBundle, GovernanceDecision, Intent, RegistrySnapshot
from ..policies import assess_reresolution
from ..repositories import CKCRepository, EvidenceRepository, GovernanceRepository
from ..services import (
    AccessHandleMaterializer,
    ActivationService,
    AssemblyService,
    CapabilityFormationService,
    EvidenceGateway,
    GovernanceService,
    ImpactAnalysisService,
    LineageService,
    ResolutionService,
    SuccessionService,
    YamlBundleMaterializer,
)
from ..services.registry_service import RegistryService
from ..specification import ArtifactValidator, SchemaLoader
from ..storage import AppendOnlyStore


class ICLA:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or Settings()
        self.store = AppendOnlyStore(self.settings.data_dir)
        self.validator = ArtifactValidator(SchemaLoader(self.settings.schema_dir))
        self.resolver = ResolutionService()
        self.assembler = AssemblyService()
        self.evidence_repository = EvidenceRepository(self.store)
        self.governance_repository = GovernanceRepository(self.store)
        self.ckc_repository = CKCRepository(self.store)
        self.evidence_gateway = EvidenceGateway(self.validator, self.evidence_repository)
        self.governance = GovernanceService(self.governance_repository)
        self.succession = SuccessionService(self.ckc_repository)
        self.formation = CapabilityFormationService(self.ckc_repository)
        self.activation = ActivationService(self.ckc_repository)
        self.lineage = LineageService()
        self.impact = ImpactAnalysisService()

    def resolve_intent(self, intent: Intent, registry: RegistrySnapshot):
        return self.resolver.resolve_intent(intent, registry)

    def get_capability(
        self,
        registry: RegistrySnapshot,
        capability_id: str,
        *,
        version_policy: str = "active",
        exact_version: int | None = None,
    ):
        capability = registry.capability(capability_id)
        if capability is None:
            return None
        lineage = (
            self.ckc_repository.list_lineage(capability.active_ckc.id)
            if capability.active_ckc is not None
            else []
        )
        active = next(
            (
                item
                for item in lineage
                if capability.active_ckc is not None
                and item.id == capability.active_ckc.id
                and item.version == capability.active_ckc.version
            ),
            None,
        )
        if version_policy == "active":
            selected = active
        elif version_policy == "latest-governed":
            selected = lineage[-1] if lineage else None
        elif version_policy == "exact":
            if exact_version is None:
                raise ValueError("The exact version policy requires exact_version")
            selected = next(
                (item for item in lineage if item.version == exact_version),
                None,
            )
        else:
            raise ValueError(f"Unsupported CKC version policy: {version_policy}")
        registry_service = RegistryService(registry)
        return {
            "capability": capability,
            "version_policy": version_policy,
            "selected_ckc": selected,
            "active_ckc": active,
            "latest_governed_ckc": lineage[-1] if lineage else None,
            "ckc_lineage": lineage,
            "relations": registry_service.relations_from(capability_id),
        }

    def assemble(self, intent, resolution, registry_snapshot, ckcs, policies=None):
        return self.assembler.assemble(intent, resolution, registry_snapshot, ckcs, policies)

    @staticmethod
    def materialize(assembly, target: str | Path, transformation: dict):
        return YamlBundleMaterializer().materialize(assembly, target, transformation)

    @staticmethod
    def materialize_access_handles(assembly, handles: list[dict], transformation: dict):
        return AccessHandleMaterializer().materialize(assembly, handles, transformation)

    @staticmethod
    def requires_reresolution(**conditions):
        return assess_reresolution(**conditions)

    def submit_evidence(self, bundle: EvidenceBundle):
        return self.evidence_gateway.submit_evidence(bundle)

    def adjudicate(
        self,
        decision: GovernanceDecision,
        *,
        reviewer: str,
        policy_refs: list[str],
    ):
        return self.governance.adjudicate(
            decision,
            reviewer=reviewer,
            policy_refs=policy_refs,
        )

    def append_successor(
        self,
        capability,
        predecessor,
        successor,
        decision,
        *,
        actor: str,
    ):
        return self.succession.append_successor(
            capability,
            predecessor,
            successor,
            decision,
            actor=actor,
        )

    def impact_analysis(self, change, **context):
        return self.impact.analyze(change, **context)

    def promote_capability(
        self,
        snapshot,
        proposal,
        initial_ckc,
        decision,
        *,
        actor: str,
    ):
        return self.formation.promote(
            snapshot,
            proposal,
            initial_ckc,
            decision,
            actor=actor,
        )

    def impact_analysis_stream(self, changes, **context):
        return self.impact.analyze_change_stream(changes, **context)

    def activate_ckc(self, snapshot, appended_lineage_ckc, decision, *, actor: str):
        updated, record = self.activation.activate(
            snapshot,
            appended_lineage_ckc,
            decision,
            actor=actor,
        )
        self.governance_repository.append_activation(record)
        return updated, record

    def rollback_ckc(self, snapshot, target, decision, *, actor: str):
        updated, record = self.activation.rollback(snapshot, target, decision, actor=actor)
        self.governance_repository.append_activation(record)
        return updated, record

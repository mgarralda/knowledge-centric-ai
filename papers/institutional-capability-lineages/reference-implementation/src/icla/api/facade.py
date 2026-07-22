"""
Institutional Capability Lineages (ICLA)
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
from ..repositories import EvidenceRepository, GovernanceRepository
from ..services import (
    AccessHandleMaterializer,
    ActivationService,
    AssemblyService,
    CrystallizationService,
    EvidenceGateway,
    GovernanceService,
    ImpactAnalysisService,
    LineageService,
    ResolutionService,
    YamlBundleMaterializer,
)
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
        self.evidence_gateway = EvidenceGateway(self.validator, self.evidence_repository)
        self.governance = GovernanceService(self.governance_repository)
        self.activation = ActivationService()
        self.lineage = LineageService()
        self.crystallization = CrystallizationService()
        self.impact = ImpactAnalysisService()

    def resolve_intent(self, intent: Intent, registry: RegistrySnapshot):
        return self.resolver.resolve_intent(intent, registry)

    @staticmethod
    def get_capability(registry: RegistrySnapshot, capability_id: str):
        return registry.capability(capability_id)

    def assemble(self, intent, resolution, registry_snapshot, ckcs, policies=None):
        return self.assembler.assemble(intent, resolution, registry_snapshot, ckcs, policies)

    @staticmethod
    def materialize(assembly, target: str | Path):
        return YamlBundleMaterializer().materialize(assembly, target)

    @staticmethod
    def materialize_access_handles(assembly, handles: list[dict]):
        return AccessHandleMaterializer().materialize(assembly, handles)

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

    def propose_capability(self, signatures, **proposal):
        return self.crystallization.propose(signatures, **proposal)

    def impact_analysis(self, change, **context):
        return self.impact.analyze(change, **context)

    def activate_ckc(self, snapshot, successor, decision, *, actor: str):
        return self.activation.activate(snapshot, successor, decision, actor=actor)

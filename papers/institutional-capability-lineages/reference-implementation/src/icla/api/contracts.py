"""
Institutional Capability Lineages (ICLA)
Reference Implementation

Copyright (c) 2026 Mariano Garralda-Barrio

Licensed under the MIT License.
See the LICENSE file in the repository root for details.
"""

# Module purpose: Technology-neutral ports corresponding to the paper's operations.

from pathlib import Path
from typing import Any, Protocol

from ..models import Assembly, EvidenceBundle, EvidenceReceipt, Intent, ResolutionResult


class RegistryPort(Protocol):
    def get_capability(self, capability_id: str) -> Any: ...


class ResolverPort(Protocol):
    def resolve_intent(self, intent: Intent, registry: Any) -> ResolutionResult: ...


class AssemblyPort(Protocol):
    def assemble(
        self,
        intent: Intent,
        resolution: ResolutionResult,
        registry_snapshot: Any,
        ckcs: list[Any],
        policies: list[str] | None = None,
    ) -> Assembly: ...


class MaterializerPort(Protocol):
    def materialize(self, assembly: Assembly, target: str | Path) -> Any: ...


class EvidenceGatewayPort(Protocol):
    def submit_evidence(self, bundle: EvidenceBundle) -> EvidenceReceipt: ...


class GovernancePort(Protocol):
    def adjudicate(self, decision: Any, *, reviewer: str, policy_refs: list[str]) -> Any: ...


class CapabilityProposalPort(Protocol):
    def propose_capability(self, signatures: list[str], **proposal: Any) -> Any: ...


class ImpactAnalysisPort(Protocol):
    def impact_analysis(self, change: dict[str, Any], **context: Any) -> Any: ...


class ActivationPort(Protocol):
    def activate_ckc(
        self,
        snapshot: Any,
        successor: Any,
        decision: Any,
        *,
        actor: str,
    ) -> Any: ...

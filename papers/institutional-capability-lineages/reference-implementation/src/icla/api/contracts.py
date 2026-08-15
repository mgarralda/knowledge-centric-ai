"""
Institutional Capability Lineage Architecture (ICLA)
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
    def get_capability(
        self,
        registry: Any,
        capability_id: str,
        *,
        version_policy: str = "active",
        exact_version: int | None = None,
    ) -> Any: ...


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
    def materialize(
        self,
        assembly: Assembly,
        target: str | Path | list[dict[str, Any]],
    ) -> Any: ...


class EvidenceGatewayPort(Protocol):
    def submit_evidence(self, bundle: EvidenceBundle) -> EvidenceReceipt: ...


class GovernancePort(Protocol):
    def adjudicate(self, decision: Any, *, reviewer: str, policy_refs: list[str]) -> Any: ...


class SuccessionPort(Protocol):
    def append_successor(
        self,
        capability: Any,
        predecessor: Any,
        successor: Any,
        decision: Any,
        *,
        actor: str,
    ) -> Any: ...


class CapabilityProposalPort(Protocol):
    def propose_capability(
        self,
        pattern: dict[str, Any],
        *,
        rationale: str,
        owner_candidate: str,
        proposed_relations: list[dict[str, Any]] | None = None,
        proposal_scoped_ckc_draft_ref: str,
    ) -> Any: ...


class CapabilityFormationPort(Protocol):
    """Governed transition to identity, approved Registry state, and initial CKC."""

    def promote_capability(
        self,
        snapshot: Any,
        proposal: Any,
        initial_ckc: Any,
        decision: Any,
        *,
        actor: str,
    ) -> Any: ...


class ImpactAnalysisPort(Protocol):
    def impact_analysis(self, change: dict[str, Any], **context: Any) -> Any: ...

    def impact_analysis_stream(self, changes: list[dict[str, Any]], **context: Any) -> Any: ...


class ActivationPort(Protocol):
    def activate_ckc(
        self,
        snapshot: Any,
        appended_lineage_ckc: Any,
        decision: Any,
        *,
        actor: str,
    ) -> Any: ...

    def rollback_ckc(
        self,
        snapshot: Any,
        target: Any,
        decision: Any,
        *,
        actor: str,
    ) -> Any: ...

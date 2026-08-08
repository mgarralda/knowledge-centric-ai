"""
Institutional Capability Lineage Architecture (ICLA)
Reference Implementation

Copyright (c) 2026 Mariano Garralda-Barrio

Licensed under the MIT License.
See the LICENSE file in the repository root for details.
"""

# Module purpose: Public information model.

from .assembly import Assembly, Materialization, OperationalMandate
from .capability import Capability, InstitutionalCapability
from .ckc import CapabilityKnowledgeContract
from .common import KnowledgeRole
from .evidence import EvidenceBundle, EvidenceReceipt
from .governance import (
    ActivationRecord,
    FormationAppendReceipt,
    GovernanceDecision,
    SuccessorAppendReceipt,
)
from .intent import Intent
from .lineage import InstitutionalCapabilityLineage, LineageEdge, LineageNode
from .proposal import CapabilityProposal, ProposalStatus
from .registry import RegistryRelation, RegistrySnapshot
from .resolution import AdmissionDecision, CandidateCapability, ResolutionResult

__all__ = [
    "ActivationRecord",
    "AdmissionDecision",
    "Assembly",
    "CandidateCapability",
    "Capability",
    "CapabilityProposal",
    "CapabilityKnowledgeContract",
    "EvidenceBundle",
    "EvidenceReceipt",
    "FormationAppendReceipt",
    "GovernanceDecision",
    "InstitutionalCapabilityLineage",
    "InstitutionalCapability",
    "Intent",
    "KnowledgeRole",
    "LineageEdge",
    "LineageNode",
    "Materialization",
    "OperationalMandate",
    "ProposalStatus",
    "RegistryRelation",
    "RegistrySnapshot",
    "ResolutionResult",
    "SuccessorAppendReceipt",
]

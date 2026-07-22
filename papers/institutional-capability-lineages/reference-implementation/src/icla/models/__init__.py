"""
Institutional Capability Lineages (ICLA)
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
from .crystallization import CapabilityProposal
from .evidence import EvidenceBundle, EvidenceReceipt
from .governance import ActivationRecord, GovernanceDecision
from .intent import Intent
from .lineage import InstitutionalCapabilityLineage, LineageEdge, LineageNode
from .registry import RegistryRelation, RegistrySnapshot
from .resolution import AdmissionDecision, CandidateCapability, ResolutionResult

__all__ = [
    "ActivationRecord",
    "AdmissionDecision",
    "Assembly",
    "CandidateCapability",
    "Capability",
    "CapabilityKnowledgeContract",
    "CapabilityProposal",
    "EvidenceBundle",
    "EvidenceReceipt",
    "GovernanceDecision",
    "InstitutionalCapabilityLineage",
    "InstitutionalCapability",
    "Intent",
    "KnowledgeRole",
    "LineageEdge",
    "LineageNode",
    "Materialization",
    "OperationalMandate",
    "RegistryRelation",
    "RegistrySnapshot",
    "ResolutionResult",
]

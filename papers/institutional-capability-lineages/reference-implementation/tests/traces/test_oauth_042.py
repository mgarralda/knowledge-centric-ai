from pathlib import Path

import pytest

from icla.models.ckc import CapabilityKnowledgeContract
from icla.models.evidence import EvidenceBundle
from icla.models.governance import GovernanceDecision
from icla.models.intent import Intent
from icla.models.registry import RegistrySnapshot
from icla.repositories import EvidenceRepository, GovernanceRepository
from icla.services import (
    ActivationService,
    EvidenceGateway,
    GovernanceService,
    LineageService,
    ResolutionService,
)
from icla.specification import (
    ArtifactValidator,
    ConformanceChecker,
    ConformanceProfile,
)
from icla.storage import AppendOnlyStore

TRACE = Path(__file__).resolve().parents[3] / "specification" / "reference-traces" / "oauth-042"


@pytest.mark.skipif(
    not TRACE.is_dir(), reason="oauth-042 reference artifacts are not published yet"
)
def test_oauth_042_trace_conforms_to_published_schemas():
    assert ArtifactValidator().validate_directory(TRACE)


@pytest.mark.skipif(
    not TRACE.is_dir(), reason="oauth-042 reference artifacts are not published yet"
)
def test_oauth_042_candidate_knowledge_cannot_claim_institutional_authority():
    validator = ArtifactValidator()
    artifacts = {path.stem: validator.validate_file(path) for path in sorted(TRACE.glob("*.yaml"))}
    artifacts["evidence-bundle"]["candidate_knowledge"][0]["institutional_authority"] = (
        "admitted"
    )

    errors = ConformanceChecker().check_trace(
        artifacts.values(), ConformanceProfile.EVOLVING
    )

    assert "ICLA-8: CEE-produced knowledge claims authority before adjudication" in errors


@pytest.mark.skipif(
    not TRACE.is_dir(), reason="oauth-042 reference artifacts are not published yet"
)
def test_oauth_042_end_to_end_governed_successor(tmp_path):
    validator = ArtifactValidator()
    artifacts = {path.stem: validator.validate_file(path) for path in sorted(TRACE.glob("*.yaml"))}
    checker = ConformanceChecker()
    checker.require_trace(artifacts.values(), ConformanceProfile.EVOLVING)

    registry = RegistrySnapshot.model_validate(artifacts["capability-registry"])
    generated_resolution = ResolutionService().resolve_intent(
        Intent.model_validate(artifacts["intent"]),
        registry,
    )
    resolution = artifacts["resolution"]
    expected_capabilities = {
        item["capability"] for item in resolution["admission"]["admitted_capabilities"]
    }
    assert generated_resolution.admission.status == "admitted"
    assert set(generated_resolution.selected_capabilities) == expected_capabilities
    assert resolution["admission"]["status"] == "admitted"
    assert {item["capability"] for item in resolution["filtering"]["excluded"]} == {
        "CAP-DATA",
        "CAP-OBS",
    }

    store = AppendOnlyStore(tmp_path)
    evidence_repository = EvidenceRepository(store)
    governance_repository = GovernanceRepository(store)
    evidence = EvidenceBundle.model_validate(artifacts["evidence-bundle"])
    assert evidence.memory_record["role"] == "episodic"
    assert artifacts["assembly"]["operational_mandate"]["authority_scope"] == (
        "execution-scoped"
    )
    assert artifacts["assembly"]["operational_mandate"][
        "institutional_change_authority"
    ] is False
    assert evidence.execution["local_execution"] == {
        "mode": "autonomous-within-mandate",
        "registry_stepwise_interaction": False,
        "working_state_disclosure": "none",
        "wholesale_working_state_capture": False,
    }
    assert evidence.execution["submission"] == {
        "selection_mode": "contract-selected",
        "checkpoint": "terminal",
    }
    assert evidence.execution["consumed_memory_roles"] == [
        "semantic",
        "procedural",
        "episodic",
    ]
    assert evidence.execution["produced_knowledge"] == {
        "status": "situated-candidate",
        "authority": "cee-or-source",
        "institutional_authority": False,
    }
    assert all(
        candidate["produced_by"] == evidence.execution["cee_ref"]
        and candidate["produced_during"] == evidence.execution["id"]
        and candidate["institutional_authority"] == "candidate-pending-adjudication"
        for candidate in evidence.candidate_knowledge
    )
    assert {
        role
        for source in artifacts["assembly"]["source_snapshot"]
        for role in source.get("knowledge_roles", [])
    } == {"semantic", "procedural", "episodic"}
    submission = evidence.model_copy(update={"status": "submitted", "gateway_receipt": None})
    receipt = EvidenceGateway(repository=evidence_repository).submit_evidence(submission)
    assert evidence.gateway_receipt is not None
    assert receipt.id == evidence.gateway_receipt.id == "RCPT-OAUTH-042"
    assert receipt.qualification_status == "qualified-for-review"
    assert all(item["passed"] is True for item in receipt.threshold_outcomes)

    decision = GovernanceDecision.model_validate(artifacts["governance-decision"])
    GovernanceService(governance_repository).adjudicate(
        decision,
        reviewer="security-and-release-governance-review",
        policy_refs=["POL-GOVERNANCE-REVIEW"],
    )
    successor = CapabilityKnowledgeContract.model_validate(artifacts["ckc-verify-v10"])
    updated, activation = ActivationService().activate(
        registry,
        successor,
        decision,
        actor="security-assurance",
    )
    governance_repository.append_activation(activation)
    assert activation.id == decision.activation["id"] == "ACT-VERIFY-010"

    assert registry.capability("CAP-VERIFY").active_ckc.version == 9
    assert updated.capability("CAP-VERIFY").active_ckc.version == 10
    assert len(updated.capabilities) == len(registry.capabilities)
    assert artifacts["assembly"]["ckc_snapshot"][4]["version"] == 9

    lineage_artifacts = list(artifacts.values()) + [
        activation.model_dump(mode="json", by_alias=True)
    ]
    lineage = LineageService().build_lineage("CAP-VERIFY", lineage_artifacts)
    LineageService.validate_connected_lineage(lineage)
    assert any(node.id == "MEM-EVD-OAUTH-042" for node in lineage.nodes)
    assert any(node.id == "CEE-OAUTH-042" for node in lineage.nodes)
    assert any(
        edge.source == "EXE-OAUTH-042"
        and edge.relation_type == "performed_by"
        and edge.target == "CEE-OAUTH-042"
        for edge in lineage.edges
    )
    assert any(
        edge.source == "EXE-OAUTH-042"
        and edge.relation_type == "operates_under"
        and edge.target == "ASM-OAUTH-042"
        for edge in lineage.edges
    )
    assert "DEC-OAUTH-042" in LineageService().trace_from_evidence("EVD-OAUTH-042", lineage)

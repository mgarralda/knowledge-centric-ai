from pathlib import Path
from types import SimpleNamespace

import pytest

from icla.models.ckc import CapabilityKnowledgeContract
from icla.models.evidence import EvidenceBundle
from icla.models.governance import GovernanceDecision
from icla.models.intent import Intent
from icla.models.registry import RegistrySnapshot
from icla.repositories import CKCRepository, EvidenceRepository, GovernanceRepository
from icla.services import (
    ActivationService,
    EvidenceGateway,
    GovernanceService,
    ImpactAnalysisService,
    LineageService,
    ResolutionService,
    SuccessionService,
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
    artifacts["evidence-bundle"]["candidate_knowledge"][0]["institutional_authority"] = "admitted"

    errors = ConformanceChecker().check_trace(artifacts.values(), ConformanceProfile.EVOLVING)

    assert "ICLA-8: CEE-produced knowledge claims authority before adjudication" in errors


@pytest.mark.skipif(
    not TRACE.is_dir(), reason="oauth-042 reference artifacts are not published yet"
)
def test_oauth_042_successor_must_reference_the_authorizing_decision():
    validator = ArtifactValidator()
    artifacts = {path.stem: validator.validate_file(path) for path in sorted(TRACE.glob("*.yaml"))}
    artifacts["ckc-verify-v10"]["generated_from"]["governance_decision"] = "DEC-OTHER"

    errors = ConformanceChecker().check_trace(artifacts.values(), ConformanceProfile.EVOLVING)

    assert "ICLA-9: successor CKC is not linked to its authorizing decision" in errors


@pytest.mark.skipif(
    not TRACE.is_dir(), reason="oauth-042 reference artifacts are not published yet"
)
def test_oauth_042_cee_configuration_is_stable_across_the_trace():
    validator = ArtifactValidator()
    artifacts = {path.stem: validator.validate_file(path) for path in sorted(TRACE.glob("*.yaml"))}
    artifacts["evidence-bundle"]["execution"]["cee_configuration_ref"] = "CEE-CONFIG-OTHER"

    errors = ConformanceChecker().check_trace(artifacts.values(), ConformanceProfile.EVOLVING)

    assert "ICLA-3/5: CEE configuration changes across the execution trace" in errors


@pytest.mark.skipif(
    not TRACE.is_dir(), reason="oauth-042 reference artifacts are not published yet"
)
def test_oauth_042_records_the_pre_resolution_iam_impact_path():
    registry_data = ArtifactValidator().validate_file(TRACE / "capability-registry.yaml")
    history = registry_data["pre_resolution_history"]

    assert history["change_event"] == {
        "id": "CHG-IDENTITY-POLICY-008",
        "source_binding_ref": "BIND-IDENTITY-POLICY",
        "source_ref": "SRC-IDENTITY-POLICY",
        "from_version": 7,
        "to_version": 8,
        "change_dimensions": ["authorized-interpretation", "temporal-validity"],
        "effect": (
            "The authorized interpretation and temporal applicability of the identity "
            "policy changed"
        ),
    }
    assert history["governance_decision"]["id"] == "DEC-IAM-008"
    assert history["successor_append"] == {
        "id": "APPEND-IAM-008",
        "capability": "CAP-IAM",
        "predecessor_ref": "CKC-IAM-v7",
        "successor_ref": "CKC-IAM-v8",
        "delta_ref": "DELTA-IAM-007-008",
        "authorization_decision_ref": "DEC-IAM-008",
        "status": "inactive-successor",
    }
    assert history["activation"]["successor_append_ref"] == "APPEND-IAM-008"
    assert history["activation"]["active_pointer_transition"] == {
        "from": "CKC-IAM-v7",
        "to": "CKC-IAM-v8",
    }
    assert history["historical_immutability"] == {
        "retained_assemblies": [
            {
                "assembly_ref": "ASM-IAM-HIST-007",
                "remains_linked_to": "CKC-IAM-v7",
            }
        ],
        "retroactive_mutation": False,
    }

    registry = RegistrySnapshot.model_validate(registry_data)
    registry.capability("CAP-IAM").active_ckc.version = 7
    iam_v7 = CapabilityKnowledgeContract(
        id="CKC-IAM",
        capability_ref="CAP-IAM",
        version=7,
        status="active",
        knowledge_scope={},
        obligations=[],
        authorities={},
        evidence_contract={},
        evaluation_contract={},
        governance={},
        projection_rules={},
        source_bindings=[{"source_ref": "SRC-IDENTITY-POLICY"}],
    )
    retained = SimpleNamespace(
        id="ASM-IAM-HIST-007",
        ckc_snapshot=[{"capability": "CAP-IAM", "ckc": "CKC-IAM", "version": 7}],
        lineage={"cee_ref": "CEE-IAM-HIST-007"},
        generated_from={"consumer": "CONSUMER-IAM-HIST-007"},
    )
    impact = ImpactAnalysisService().analyze(
        history["change_event"],
        registry=registry,
        ckcs=[iam_v7],
        assemblies=[retained],
    )

    assert impact.affected_bindings == ("BIND-IDENTITY-POLICY",)
    assert set(impact.affected_capabilities) == set(
        history["impact_record"]["affected_capabilities"]
    )
    assert {tuple(item.values()) for item in impact.traversed_relations} == {
        (item["type"], item["from"], item["to"])
        for item in history["impact_record"]["traversed_relations"]
    }
    assert impact.retained_assemblies == ("ASM-IAM-HIST-007",)
    assert impact.affected_cees == ("CEE-IAM-HIST-007",)

    lineage = LineageService().build_lineage("CAP-IAM", [registry_data])
    reachable = LineageService().trace_from_change("CHG-IDENTITY-POLICY-008", lineage)
    assert {
        "BIND-IDENTITY-POLICY",
        "IMP-IAM-008",
        "DEC-IAM-008",
        "DELTA-IAM-007-008",
        "ACT-IAM-008",
        "CKC-IAM@7",
        "CKC-IAM@8",
        "ASM-IAM-HIST-007",
    } <= reachable


@pytest.mark.skipif(
    not TRACE.is_dir(), reason="oauth-042 reference artifacts are not published yet"
)
def test_oauth_042_rejects_a_temporally_invalid_identity_policy_binding():
    validator = ArtifactValidator()
    registry_data = validator.validate_file(TRACE / "capability-registry.yaml")
    intent_data = validator.validate_file(TRACE / "intent.yaml")
    registry_data["source_bindings"][0]["temporal_validity"]["status"] = "superseded"

    result = ResolutionService().resolve_intent(
        Intent.model_validate(intent_data),
        RegistrySnapshot.model_validate(registry_data),
    )

    iam_validation = next(
        item for item in result.constraint_validation if item["capability"] == "CAP-IAM"
    )
    assert iam_validation["source_bindings_temporally_valid"] is False
    assert "CAP-IAM" not in {item.capability for item in result.admission.admitted_capabilities}


@pytest.mark.skipif(
    not TRACE.is_dir(), reason="oauth-042 reference artifacts are not published yet"
)
def test_oauth_042_successor_must_reference_the_decision_linked_delta():
    validator = ArtifactValidator()
    artifacts = {path.stem: validator.validate_file(path) for path in sorted(TRACE.glob("*.yaml"))}
    artifacts["ckc-verify-v10"]["governance"]["successor_delta_ref"] = "DELTA-OTHER"

    errors = ConformanceChecker().check_trace(artifacts.values(), ConformanceProfile.EVOLVING)

    assert "ICLA-9: complete successor CKC is not linked to the decision successor delta" in errors


@pytest.mark.skipif(
    not TRACE.is_dir(), reason="oauth-042 reference artifacts are not published yet"
)
def test_oauth_042_successor_delta_must_retain_supporting_evidence():
    validator = ArtifactValidator()
    artifacts = {path.stem: validator.validate_file(path) for path in sorted(TRACE.glob("*.yaml"))}
    artifacts["governance-decision"]["successor_delta"]["supporting_evidence_refs"] = [
        "EVD-OAUTH-042"
    ]

    errors = ConformanceChecker().check_trace(artifacts.values(), ConformanceProfile.EVOLVING)

    assert "ICLA-9: successor delta omits its supporting evidence or receipt" in errors


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
    assert (
        next(
            item
            for item in generated_resolution.constraint_validation
            if item["capability"] == "CAP-IAM"
        )["source_bindings_temporally_valid"]
        is True
    )

    store = AppendOnlyStore(tmp_path)
    evidence_repository = EvidenceRepository(store)
    governance_repository = GovernanceRepository(store)
    ckc_repository = CKCRepository(store)
    evidence = EvidenceBundle.model_validate(artifacts["evidence-bundle"])
    assert evidence.memory_record["role"] == "episodic"
    assert artifacts["assembly"]["operational_mandate"]["authority_scope"] == ("execution-scoped")
    assert artifacts["assembly"]["operational_mandate"]["institutional_change_authority"] is False
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
    assert decision.activation["rollback_target"] == "CKC-VERIFY-v9"
    assert decision.successor_delta == {
        "id": "DELTA-VERIFY-009-010",
        "predecessor_ref": "CKC-VERIFY-v9",
        "successor_ref": "CKC-VERIFY-v10",
        "changed_commitments": [
            {
                "area": "knowledge_scope",
                "operation": "add",
                "subject": "reusable-compatibility-test-pattern",
            },
            {
                "area": "evaluation_contract",
                "operation": "add",
                "subject": "api.client.compatibility",
            },
        ],
        "rationale": (
            "Qualified OAuth evidence supports reuse of the compatibility-test pattern "
            "within the existing CAP-VERIFY responsibility."
        ),
        "supporting_evidence_refs": ["EVD-OAUTH-042", "RCPT-OAUTH-042"],
        "authorization_decision_ref": "DEC-OAUTH-042",
        "rollback_ref": "CKC-VERIFY-v9",
        "successor_complete": True,
        "reconstruction_patch": False,
    }
    assert decision.impact_record["assessment_mode"] == "continuous-event-driven"
    proposals = decision.capability_formation["proposals"]
    assert [proposal["id"] for proposal in proposals] == ["PROP-AUTH-EVOL-01"]
    assert proposals[0]["stable_assembly_rules"]
    assert proposals[0]["value_assessment"]
    GovernanceService(governance_repository).adjudicate(
        decision,
        reviewer="security-and-release-governance-review",
        policy_refs=["POL-GOVERNANCE-REVIEW"],
    )
    successor = CapabilityKnowledgeContract.model_validate(artifacts["ckc-verify-v10"])
    predecessor = successor.model_copy(
        deep=True,
        update={
            "version": 9,
            "status": "canonical-active",
            "predecessor": "CKC-VERIFY-v8",
            "generated_from": {"retained_lineage": "CKC-VERIFY-v9"},
            "governance": {},
        },
    )
    ckc_repository.append_successor(predecessor)
    append_receipt = SuccessionService(ckc_repository).append_successor(
        registry.capability("CAP-VERIFY"),
        predecessor,
        successor,
        decision,
        actor="security-assurance",
    )
    assert registry.capability("CAP-VERIFY").active_ckc.version == 9
    assert append_receipt.id == decision.successor_append["id"]
    assert append_receipt.status == "inactive-successor"

    updated, activation = ActivationService(ckc_repository).activate(
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
        append_receipt.model_dump(mode="json", by_alias=True),
        activation.model_dump(mode="json", by_alias=True),
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
        and edge.relation_type == "configured_as"
        and edge.target == "CEE-CONFIG-OAUTH-042"
        for edge in lineage.edges
    )
    assert any(
        edge.source == "EXE-OAUTH-042"
        and edge.relation_type == "operates_under"
        and edge.target == "ASM-OAUTH-042"
        for edge in lineage.edges
    )
    assert "DEC-OAUTH-042" in LineageService().trace_from_evidence("EVD-OAUTH-042", lineage)
    assert any(
        edge.source == "DEC-OAUTH-042"
        and edge.relation_type == "authorizes"
        and edge.target == "DELTA-VERIFY-009-010"
        for edge in lineage.edges
    )
    assert any(
        edge.source == "DELTA-VERIFY-009-010"
        and edge.relation_type == "supported_by"
        and edge.target == "EVD-OAUTH-042"
        for edge in lineage.edges
    )

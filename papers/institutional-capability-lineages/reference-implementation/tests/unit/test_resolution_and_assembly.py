import pytest

from icla.exceptions import AdmissionError
from icla.models.capability import ActiveCKC, Capability
from icla.models.ckc import CapabilityKnowledgeContract
from icla.models.intent import Intent
from icla.models.registry import RegistryRelation, RegistrySnapshot
from icla.policies.conflict_resolution import resolve_obligation_conflicts
from icla.services.assembly_service import AssemblyService
from icla.services.registry_service import RegistryService
from icla.services.resolution_service import ResolutionService
from icla.specification import ArtifactValidator


def capability(identifier, outcome, *, lifecycle="active"):
    suffix = identifier.removeprefix("CAP-")
    return Capability(
        id=identifier,
        name=suffix,
        outcome=outcome,
        owner="OWNER",
        domain="security",
        lifecycle=lifecycle,
        active_ckc=ActiveCKC(id=f"CKC-{suffix}", version=1),
    )


def registry(*, include_conflict=False):
    capabilities = [
        capability("CAP-AUTH", "authentication change"),
        capability("CAP-DEP", "release governance"),
        capability("CAP-SHARED", "observability"),
        capability("CAP-ALT", "authentication change", lifecycle="retired"),
    ]
    relations = [
        RegistryRelation.model_validate(
            {"type": "depends_on", "from": "CAP-AUTH", "to": "CAP-DEP"}
        ),
        RegistryRelation.model_validate(
            {"type": "shares_knowledge", "from": "CAP-AUTH", "to": "CAP-SHARED"}
        ),
    ]
    if include_conflict:
        capabilities.append(capability("CAP-CONFLICT", "conflicting control"))
        relations.append(
            RegistryRelation.model_validate(
                {
                    "type": "conflicts_with",
                    "from": "CAP-AUTH",
                    "to": "CAP-CONFLICT",
                }
            )
        )
    return RegistrySnapshot(
        id="REG-SNAP-TEST",
        generated_from={"source": "test"},
        registry={
            "logical_registry_id": "REG",
            "snapshot_status": "immutable",
            "capability_count": len(capabilities),
            "active_pointer_policy": "governed",
        },
        capabilities=capabilities,
        relations=relations,
    )


def intent(*outcomes):
    return Intent(
        id="INT-TEST",
        schema_ref="schemas/intent.schema.yaml",
        generated_from={"source": "test"},
        goal="change authentication",
        context={},
        cee={"id": "CEE-TEST", "type": "agent", "consumer_configuration_id": "AGENT-1"},
        consumer={"type": "agent", "configuration_id": "AGENT-1"},
        risk={"level": "high"},
        budget={"max_capabilities": 5},
        assurance={"level": "high"},
        required_outcomes=list(outcomes),
    )


def ckc(capability_id):
    suffix = capability_id.removeprefix("CAP-")
    return CapabilityKnowledgeContract(
        id=f"CKC-{suffix}",
        generated_from={"source": "test"},
        capability_ref=capability_id,
        version=1,
        status="active",
        knowledge_scope={"outcomes": ["authentication change"]},
        obligations=[],
        evidence_contract={},
        evaluation_contract={
            "metrics": [
                {
                    "metric_id": f"metric.{suffix.lower()}",
                    "authority": f"CKC-{suffix}-v1",
                }
            ]
        },
        governance={"authority": "OWNER"},
        projection_rules={},
        source_bindings=[
            {
                "id": f"BIND-{suffix}",
                "source": f"SRC-{suffix}",
                "version": 1,
                "authority": "OWNER",
            }
        ],
    )


def test_only_mandatory_relations_expand_and_irrelevant_exclusions_do_not_make_partial():
    result = ResolutionService().resolve_intent(intent("authentication change"), registry())

    assert result.admission.status == "admitted"
    assert set(result.selected_capabilities) == {"CAP-AUTH", "CAP-DEP"}
    assert "CAP-SHARED" not in result.relation_expansion["capabilities"]
    assert result.relation_expansion["advisory_relations"][0]["type"] == "shares_knowledge"
    assert any(item["capability"] == "CAP-ALT" for item in result.filtering["excluded"])
    ArtifactValidator().validate_artifact(result.model_dump(mode="json", by_alias=True))


def test_registry_filters_metadata_policy_and_conditions():
    snapshot = registry()
    capability_item = snapshot.capability("CAP-AUTH")
    capability_item.policy_refs = ["POL-AUTH-v1"]
    capability_item.conditions = {"assurance": "high"}

    matches = RegistryService(snapshot).filter(
        owner="OWNER",
        policy_ref="POL-AUTH-v1",
        conditions={"assurance": "high"},
    )

    assert [item.id for item in matches] == ["CAP-AUTH"]


def test_simultaneously_admitted_conflicting_capabilities_are_partial():
    result = ResolutionService().resolve_intent(
        intent("authentication change", "conflicting control"),
        registry(include_conflict=True),
    )

    assert result.admission.status == "partial"
    assert result.conflict_resolution["status"] == "unresolved"


def test_assembly_checks_actual_required_outcome_coverage():
    snapshot = registry()
    original_intent = intent("authentication change")
    resolution = ResolutionService().resolve_intent(original_intent, snapshot)
    contracts = [ckc("CAP-AUTH"), ckc("CAP-DEP")]

    assembly = AssemblyService().assemble(
        original_intent,
        resolution,
        snapshot,
        contracts,
    )
    assert assembly.correctness["required_covered"] is True
    ArtifactValidator().validate_artifact(assembly.model_dump(mode="json", by_alias=True))

    uncovered_intent = original_intent.model_copy(
        update={"required_outcomes": ["unrepresented outcome"]}
    )
    with pytest.raises(AdmissionError, match="required_covered"):
        AssemblyService().assemble(
            uncovered_intent,
            resolution,
            snapshot,
            contracts,
        )


def test_incompatible_obligations_remain_unresolved():
    _, rationale, unresolved = resolve_obligation_conflicts(
        [
            {"id": "OBL-1", "mode": "allow"},
            {"id": "OBL-1", "mode": "deny"},
        ]
    )
    assert unresolved
    assert "governance review" in rationale[0]

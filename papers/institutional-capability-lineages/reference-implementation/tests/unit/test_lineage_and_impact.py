from icla.models.capability import ActiveCKC, Capability
from icla.models.ckc import CapabilityKnowledgeContract
from icla.models.registry import RegistrySnapshot
from icla.services.impact_analysis_service import ImpactAnalysisService
from icla.services.lineage_service import LineageService


def test_lineage_edges_are_extracted_from_each_artifact_type():
    artifacts = [
        {
            "document_type": "capability-resolution",
            "id": "RES-1",
            "intent_ref": "INT-1",
            "registry_snapshot_ref": "REG-SNAP-1",
            "admission": {
                "id": "ADM-1",
                "admitted_capabilities": [{"capability": "CAP-1", "ckc": "CKC-1", "version": 1}],
            },
        },
        {
            "document_type": "contextual-assembly",
            "id": "ASM-1",
            "lineage": {
                "intent_ref": "INT-1",
                "registry_snapshot_ref": "REG-SNAP-1",
                "resolution_ref": "RES-1",
                "admission_ref": "ADM-1",
            },
            "ckc_snapshot": [{"ckc": "CKC-1", "version": 1}],
        },
        {
            "document_type": "execution-evidence-bundle",
            "id": "EVD-1",
            "execution": {
                "id": "EXE-1",
                "cee_ref": "CEE-1",
                "materialization_ref": "MAT-1",
            },
            "lineage": {"assembly_ref": "ASM-1"},
            "candidate_knowledge": [
                {
                    "id": "CAND-1",
                    "produced_by": "CEE-1",
                    "produced_during": "EXE-1",
                }
            ],
            "memory_record": {"id": "MEM-1"},
        },
        {
            "document_type": "governance-decision",
            "id": "DEC-1",
            "inputs": {"evidence_ref": "EVD-1", "assembly_ref": "ASM-1"},
            "resulting_lineage_edges": [],
        },
    ]

    lineage = LineageService().build_lineage("CAP-1", artifacts)

    relation_types = {edge.relation_type for edge in lineage.edges}
    assert {
        "derived_from",
        "admits",
        "uses",
        "consumes",
        "performed_by",
        "produced_during",
        "submitted_as",
        "adjudicates",
    } <= relation_types
    LineageService.validate_connected_lineage(lineage)


def test_impact_analysis_uses_exact_structured_references():
    capability = Capability(
        id="CAP-1",
        name="One",
        outcome="one",
        owner="OWNER",
        domain="test",
        lifecycle="active",
        active_ckc=ActiveCKC(id="CKC-1", version=1),
    )
    registry = RegistrySnapshot(
        id="REG-SNAP-1",
        generated_from={"source": "test"},
        registry={
            "logical_registry_id": "REG",
            "snapshot_status": "immutable",
            "capability_count": 1,
            "active_pointer_policy": "governed",
        },
        capabilities=[capability],
        relations=[],
    )
    contract = CapabilityKnowledgeContract(
        id="CKC-1",
        generated_from={"source": "test"},
        capability_ref="CAP-1",
        version=1,
        status="active",
        knowledge_scope={},
        obligations=[],
        evidence_contract={},
        evaluation_contract={},
        governance={},
        projection_rules={},
        source_bindings=[{"source_ref": "SRC-10"}],
    )
    service = ImpactAnalysisService()

    accidental = service.analyze(
        {"source_ref": "SRC-1"}, registry=registry, ckcs=[contract], assemblies=[]
    )
    exact = service.analyze(
        {"source_ref": "SRC-10"}, registry=registry, ckcs=[contract], assemblies=[]
    )

    assert accidental.affected_ckcs == ()
    assert exact.affected_ckcs == ("CKC-1",)

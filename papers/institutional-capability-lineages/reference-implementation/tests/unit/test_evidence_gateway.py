from icla.models.evidence import EvidenceBundle
from icla.repositories.evidence_repository import EvidenceRepository
from icla.services.evidence_gateway import EvidenceGateway
from icla.specification import ArtifactValidator
from icla.storage import AppendOnlyStore


def bundle():
    return EvidenceBundle(
        id="EVD-TEST",
        schema_ref="schemas/evidence-bundle.schema.yaml",
        generated_from={"execution": "EXE-1", "assembly": "ASM-1", "producer": "P-1"},
        status="submitted",
        execution={
            "id": "EXE-1",
            "cee_ref": "CEE-1",
            "consumer": "AGENT-1",
            "materialization_ref": "MAT-1",
        },
        lineage={
            "intent_ref": "INT-1",
            "registry_snapshot_ref": "REG-SNAP-1",
            "resolution_ref": "RES-1",
            "admission_ref": "ADM-1",
            "assembly_ref": "ASM-1",
            "exact_ckc_versions": ["CKC-VERIFY@9"],
            "source_versions": ["SRC-1@1"],
        },
        results={},
        artifacts=[{"id": "ART-1"}],
        measurements={
            "governed": [
                {
                    "metric_id": "verify.latency",
                    "value": 10,
                    "unit": "minutes",
                    "collection_condition": "complete-validation-run",
                    "governed_definition": "METRIC-VERIFY-LATENCY@1",
                    "threshold": {"operator": "<=", "value": 5},
                    "conformity": "conforming",
                    "result": "fail",
                }
            ],
            "nonstandard": [],
        },
        memory_record={
            "id": "MEM-EVD-TEST",
            "role": "episodic",
            "lineage_status": "retained",
            "institutional_authority": "candidate-pending-adjudication",
        },
        candidate_knowledge=[],
    )


def test_conforming_failed_metric_is_qualified_and_persisted(tmp_path):
    repository = EvidenceRepository(AppendOnlyStore(tmp_path))
    receipt = EvidenceGateway(repository=repository).submit_evidence(bundle())

    assert receipt.metric_conformity is True
    assert receipt.id == "RCPT-TEST"
    assert receipt.threshold_outcomes[0]["passed"] is False
    assert receipt.qualification_status == "qualified-for-review"
    assert repository.get("EVD-TEST").status == "qualified-for-review"
    assert repository.get_receipt(receipt.id) == receipt
    ArtifactValidator().validate_artifact(
        repository.get("EVD-TEST").model_dump(mode="json", by_alias=True, exclude_none=True)
    )

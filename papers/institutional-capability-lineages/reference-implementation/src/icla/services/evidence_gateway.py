"""
Institutional Capability Lineages (ICLA)
Reference Implementation

Copyright (c) 2026 Mariano Garralda-Barrio

Licensed under the MIT License.
See the LICENSE file in the repository root for details.
"""

# Module purpose: Qualify evidence without adjudicating its institutional meaning.

from ..models.evidence import EvidenceBundle, EvidenceReceipt
from ..policies.evaluation import evaluate_metric
from ..repositories.evidence_repository import EvidenceRepository
from ..specification.validator import ArtifactValidator


class EvidenceGateway:
    def __init__(
        self,
        validator: ArtifactValidator | None = None,
        repository: EvidenceRepository | None = None,
    ) -> None:
        self.validator = validator or ArtifactValidator()
        self.repository = repository

    def submit_evidence(self, bundle: EvidenceBundle) -> EvidenceReceipt:
        submission = bundle.model_copy(update={"status": "submitted", "gateway_receipt": None})
        data = submission.model_dump(mode="json", by_alias=True, exclude_none=True)
        schema_ok, rationale = True, []
        try:
            self.validator.validate_artifact(data, "evidence-bundle")
        except Exception as error:
            schema_ok = False
            rationale.append(str(error))
        governed = bundle.measurements.get("governed", [])
        metric_results = [evaluate_metric(item) for item in governed]
        metric_ok = bool(governed) and all(
            result.definition_conformity for result in metric_results
        )
        provenance_ok = all(
            bundle.lineage.get(key)
            for key in (
                "intent_ref",
                "registry_snapshot_ref",
                "resolution_ref",
                "admission_ref",
                "assembly_ref",
                "exact_ckc_versions",
                "source_versions",
            )
        )
        qualified = schema_ok and metric_ok and provenance_ok
        receipt_id = (
            f"RCPT-{bundle.id.removeprefix('EVD-')}"
            if bundle.id.startswith("EVD-")
            else f"RCPT-{bundle.id}"
        )
        receipt = EvidenceReceipt(
            id=receipt_id,
            schema_conformity=schema_ok,
            metric_conformity=metric_ok,
            provenance_complete=provenance_ok,
            qualification_status="qualified-for-review" if qualified else "rejected",
            threshold_outcomes=[
                {
                    "metric_id": measurement.get("metric_id"),
                    "passed": result.threshold_passed,
                    "rationale": result.rationale,
                }
                for measurement, result in zip(governed, metric_results, strict=True)
            ],
            rationale=rationale
            + [result.rationale for result in metric_results if result.threshold_passed is False],
        )
        if self.repository is not None:
            qualified_bundle = submission.model_copy(
                update={
                    "gateway_receipt": receipt,
                    "status": ("qualified-for-review" if qualified else "rejected"),
                }
            )
            self.repository.append(qualified_bundle)
            self.repository.append_receipt(receipt)
        return receipt

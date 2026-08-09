from icla.specification.conformance import check_icla_8_evidence_separation


def test_measurement_channels_are_separate():
    assert not check_icla_8_evidence_separation(
        {
            "document_type": "execution-evidence-bundle",
            "measurements": {"governed": [], "nonstandard": []},
        }
    )


def test_submitted_report_transformation_is_optional_but_versioned_when_present():
    evidence = {
        "document_type": "execution-evidence-bundle",
        "measurements": {"governed": [], "nonstandard": []},
        "lineage": {
            "submitted_report_transformations": [
                {"id": "TRANSFORM-EVIDENCE-REPORT", "version": 1}
            ]
        },
    }

    assert not check_icla_8_evidence_separation(evidence)
    del evidence["lineage"]["submitted_report_transformations"][0]["version"]
    assert (
        "ICLA-8: submitted-report transformation is not version-referenced"
        in check_icla_8_evidence_separation(evidence)
    )

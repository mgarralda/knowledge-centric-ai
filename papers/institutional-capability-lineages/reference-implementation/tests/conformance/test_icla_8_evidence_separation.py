from icla.specification.conformance import check_icla_8_evidence_separation


def test_measurement_channels_are_separate():
    assert not check_icla_8_evidence_separation(
        {
            "document_type": "execution-evidence-bundle",
            "measurements": {"governed": [], "nonstandard": []},
        }
    )

from __future__ import annotations


def test_formulation_coverage_validator_enforces_qku_and_family_mapping(records):
    audit = records("PR162D_R2A_FormulationCoverageAudit.report.json")[0]
    assert audit["validation_status"] == "PASS"
    assert audit["formulation_backed_qku_count"] > audit["field_fill_qku_count"]
    assert audit["field_fill_qku_percentage"] <= 25.0
    assert audit["field_fill_without_mapping_attempt_count"] == 0
    assert audit["normalized_family_unmapped_percentage"] <= 25.0
    assert audit["packet_only_qku_count"] == 0
    assert audit["route_only_qku_count"] == 0
    assert audit["metadata_only_qku_count"] == 0
    assert audit["quantum_label_only_qku_count"] == 0
    assert audit["sample_mapping_attempts"]
    assert all(sample["mapping_attempted_flag"] for sample in audit["sample_mapping_attempts"])

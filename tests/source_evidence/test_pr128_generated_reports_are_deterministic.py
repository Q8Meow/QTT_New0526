from tests.source_evidence.pr128_cross_venue_execution_normalization_support import (
    artifacts,
    generated_report_payloads,
)


def test_pr128_generated_reports_are_deterministic():
    first = artifacts()
    second = artifacts()
    generated = generated_report_payloads()

    assert first == second
    assert generated["main_report"] == first["main_report"]
    assert generated["binding_report"] == first["binding_report"]
    assert generated["taxonomy_report"] == first["taxonomy_report"]
    assert generated["downstream_handoff_report"] == first["downstream_handoff_report"]

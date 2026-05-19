from tests.source_evidence.pr127_execution_lifecycle_support import (
    artifacts,
    generated_report_payloads,
)


def test_pr127_generated_reports_are_deterministic():
    first = artifacts()
    second = artifacts()
    generated = generated_report_payloads()

    assert first == second
    assert generated["main_report"] == first["main_report"]
    assert generated["builder_report"] == first["builder_report"]
    assert generated["models_report"] == first["models_report"]
    assert generated["handoff_report"] == first["handoff_report"]

import json

from tests.source_evidence.pr126_connector_semantic_implementation_support import (
    artifacts,
    generated_report_payloads,
)


def test_pr126_generated_reports_are_deterministic():
    first = artifacts()
    second = artifacts()

    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)
    assert generated_report_payloads() == first
    assert first["main_report"]["deterministic_fixture_time_used"] is True

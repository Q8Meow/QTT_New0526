from tests.source_evidence import pr129_runtime_cash_component_field_map_support as support


def test_generated_reports_are_deterministic():
    expected = support.artifacts()
    generated = support.generated_report_payloads()

    assert generated == expected
